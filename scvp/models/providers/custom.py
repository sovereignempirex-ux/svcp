"""Local model provider backed by Transformers or llama.cpp."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any, Iterable, List, Optional

from scvp.core.exceptions import ModelError, SCVPTimeoutError
from scvp.core.types import Message, ModelResponse, Role, StreamChunk, Usage
from scvp.models.base import ModelProvider, model_registry


class CustomModelProvider(ModelProvider):
    """Run a local Transformers or GGUF model without an external service.

    ``model`` is intentionally injectable so applications and tests can use a
    compatible lightweight backend without loading a large model.
    """

    name = "custom"

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_name: Optional[str] = None,
        device: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 512,
        timeout: Optional[float] = None,
        backend: str = "auto",
        model: Any = None,
        tokenizer: Any = None,
    ):
        if temperature < 0:
            raise ValueError("temperature must be non-negative")
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")
        self.model_path = Path(model_path).expanduser() if model_path else None
        self.model_name = model_name or (self.model_path.name if self.model_path else "custom-local")
        self.device = device
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.backend = backend
        self._model = model
        self._tokenizer = tokenizer

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        if self.model_path is None:
            raise ModelError("Custom provider requires model_path or an injected model.")
        if not self.model_path.exists():
            raise ModelError(f"Local model path does not exist: '{self.model_path}'")

        backend = self.backend
        if backend == "auto":
            backend = "llama_cpp" if self.model_path.suffix.lower() == ".gguf" else "transformers"
        if backend == "llama_cpp":
            try:
                from llama_cpp import Llama
            except ImportError as exc:
                raise ModelError("Install llama-cpp-python to load GGUF models.") from exc
            self._model = Llama(model_path=str(self.model_path))
            return
        if backend != "transformers":
            raise ModelError(f"Unsupported custom model backend: '{backend}'")
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ModelError("Install transformers and torch to load local models.") from exc
        try:
            import torch

            resolved_device = self.device
            if resolved_device == "auto":
                resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self._model = AutoModelForCausalLM.from_pretrained(str(self.model_path))
            self._model.to(resolved_device)
            self._model.eval()
            self.device = resolved_device
        except Exception as exc:
            raise ModelError(f"Could not load local Transformers model '{self.model_path}': {exc}") from exc

    @staticmethod
    def _prompt(messages: List[Message]) -> str:
        return "\n".join(f"{message.role.value}: {message.content}" for message in messages)

    def _call(self, messages: List[Message], **kwargs: Any) -> str:
        self._ensure_loaded()
        prompt = self._prompt(messages)
        max_tokens = int(kwargs.get("max_tokens", self.max_tokens))
        temperature = float(kwargs.get("temperature", self.temperature))
        if hasattr(self._model, "create_completion"):
            result = self._model.create_completion(
                prompt, max_tokens=max_tokens, temperature=temperature, stream=False
            )
            return result["choices"][0]["text"]
        if hasattr(self._model, "generate") and self._tokenizer is not None:
            inputs = self._tokenizer(prompt, return_tensors="pt")
            if self.device:
                inputs = {key: value.to(self.device) for key, value in inputs.items()}
            output = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-5),
                pad_token_id=self._tokenizer.eos_token_id,
            )
            generated = output[0][inputs["input_ids"].shape[-1] :]
            return self._tokenizer.decode(generated, skip_special_tokens=True)
        if hasattr(self._model, "generate"):
            result = self._model.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            return result.content if isinstance(result, ModelResponse) else str(result)
        raise ModelError("Injected custom model must provide generate() or create_completion().")

    def _run_with_timeout(self, messages: List[Message], **kwargs: Any) -> str:
        if self.timeout is None:
            return self._call(messages, **kwargs)
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._call, messages, **kwargs)
        try:
            return future.result(timeout=self.timeout)
        except FutureTimeoutError as exc:
            future.cancel()
            raise SCVPTimeoutError(
                f"Custom model generation exceeded timeout ({self.timeout}s)."
            ) from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def chat(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        content = self._run_with_timeout(messages, **kwargs)
        prompt = self._prompt(messages)
        return ModelResponse(
            content=content,
            model=self.model_name,
            provider=self.name,
            usage=Usage(
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(content.split()),
                total_tokens=len(prompt.split()) + len(content.split()),
            ),
            finish_reason="stop",
        )

    def stream(self, messages: List[Message], **kwargs: Any) -> Iterable[StreamChunk]:
        response = self.chat(messages, **kwargs)
        words = response.content.split(" ")
        for index, word in enumerate(words):
            yield StreamChunk(delta=word + (" " if index < len(words) - 1 else ""))
        yield StreamChunk(delta="", done=True, finish_reason="stop")


model_registry.register("custom", CustomModelProvider, override=True)