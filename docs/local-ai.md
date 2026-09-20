# Local AI

The `local` provider runs a model from the filesystem. It does not call OpenAI, Google, or another hosted API.

## Transformers

```bash
python -m pip install -e ".[local-models]"
```

```python
from scvp import Message, Role, SCVPModel

model = SCVPModel(
    provider="local",
    model_path="./models/my-model",
    device="auto",
    max_tokens=256,
)
response = model.chat([Message(Role.USER, "Summarize this project")])
print(response.content)
```

The directory must contain the files expected by `AutoTokenizer` and `AutoModelForCausalLM`.

## GGUF

```bash
python -m pip install -e ".[gguf]"
```

```python
model = SCVPModel(provider="local", model_path="./models/model.gguf")
```

Model loading is lazy. A missing path or missing backend produces a typed error when the first request is made. Model weights are intentionally not included in the repository; keep them in a local `models/` directory and do not commit them.
