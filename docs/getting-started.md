# Getting Started

## Install

```bash
python -m pip install scvp
```

For development from this repository:

```bash
python -m pip install -e ".[dev]"
```

## First model call

```python
from scvp import Message, Role, SCVPModel

model = SCVPModel(provider="mock")
response = model.chat([Message(Role.USER, "Hello, SCVP")])
print(response.content)
```

## Agent

```python
from scvp import Agent

result = Agent(name="support").run("Explain the project")
print(result.content)
```

## CLI

```bash
scvp --version
scvp model list
scvp agent run "Explain SCVP"
scvp plugin list
scvp test
```

Use `mock` for deterministic development. Use `local` when a real model file is available.
