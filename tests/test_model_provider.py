import pytest

from scvp import Message, Role, SCVPModel
from scvp.core.exceptions import ModelCapabilityNotSupportedError
from scvp.core.types import ModelResponse
from scvp.models.base import ModelProvider, model_registry


def test_mock_chat():
    model = SCVPModel(provider="mock")
    response = model.chat([Message(role=Role.USER, content="hello there")])
    assert "hello there" in response.content
    assert response.provider == "mock"
    assert response.usage.total_tokens > 0


def test_mock_generate():
    model = SCVPModel(provider="mock")
    response = model.generate("what's up")
    assert response.provider == "mock"
    assert "what's up" in response.content


def test_mock_stream():
    model = SCVPModel(provider="mock")
    chunks = list(model.stream([Message(role=Role.USER, content="stream this")]))
    assert chunks[-1].done is True
    joined = "".join(c.delta for c in chunks)
    assert "stream this" in joined


def test_mock_embed():
    model = SCVPModel(provider="mock")
    vectors = model.embed(["a", "b"])
    assert len(vectors) == 2
    assert all(len(v) == 8 for v in vectors)


def test_mock_embed_is_deterministic():
    model = SCVPModel(provider="mock")
    assert model.embed(["same text"]) == model.embed(["same text"])


def test_mock_classify():
    model = SCVPModel(provider="mock")
    label = model.classify("some text", ["a", "b", "c"])
    assert label in ["a", "b", "c"]


def test_mock_reason_defaults_to_chat():
    model = SCVPModel(provider="mock")
    response = model.reason([Message(role=Role.USER, content="think about this")])
    assert response.provider == "mock"


def test_capability_not_supported_raises_clear_error():
    class BareProvider(ModelProvider):
        name = "bare"

        def chat(self, messages, **kwargs):
            return ModelResponse(content="ok", model="bare-1", provider=self.name)

    model_registry.register("bare", BareProvider, override=True)
    model = SCVPModel(provider="bare")

    with pytest.raises(ModelCapabilityNotSupportedError) as exc_info:
        model.embed(["x"])

    assert "bare" in str(exc_info.value)
    assert "embed" in str(exc_info.value)
