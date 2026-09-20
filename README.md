# SCVP — Provider-Agnostic Agent Runtime

SCVP is a small, provider-agnostic Python runtime for building AI agents.
It provides one stable model interface, deterministic local providers,
configurable agent execution, and injectable tools without locking an
application to a vendor SDK.

> **Status:** Phases 0 through 13 are implemented and covered by the test
> suite. Optional integrations require their documented extras.

## Documentation

Start with the [documentation index](docs/README.md) for focused guides on
installation, local AI, RAG, API security, plugins, SDKs, testing, and release.

## Model providers

The built-in `mock` provider is deterministic and requires no API key. It
implements the complete model surface (`generate`, `chat`, `stream`,
`embed`, `classify`, and `reason`) so applications and tests can run locally.
Additional providers can register against the same `SCVPModel` interface.

### Local Custom Model

`CustomModelProvider` runs a model from disk without an API key or external
service. Install the optional backend you need:

```bash
pip install -e ".[local-models]"       # Hugging Face Transformers + torch
pip install -e ".[gguf]"               # GGUF through llama-cpp-python
```

Download a compatible model into a local directory (for example from a model
repository using its normal download tools), then point the configuration at
that directory. Transformers directories are loaded with
`AutoTokenizer`/`AutoModelForCausalLM`; a `.gguf` path uses llama.cpp.

Complete `scvp.config.yaml` example:

```yaml
models:
  default: custom
  providers:
    custom:
      type: custom
      model_path: "./models/my-model"
      device: "auto"
      temperature: 0.7
      max_tokens: 512
      timeout: 120
```

Create a model from that configuration and use it with an Agent:

```python
from scvp import Agent, SCVPModel, load_config

config = load_config("scvp.config.yaml")
model = SCVPModel.from_config(config)
agent = Agent(name="local-support", model=model)
result = agent.run("Summarize this project.")
print(result.content)
```

Loading is lazy: `transformers`, `torch`, or `llama-cpp-python` are imported
only when the custom provider receives its first request. Tests can inject any
lightweight object with a `generate()` method, so they never need a large model.

### Independent Local AI

The `local` provider runs a real model from disk without OpenAI, Google, or any
hosted API. Install the backend you need:

```bash
pip install -e ".[local-models]"  # Transformers + torch
pip install -e ".[gguf]"           # GGUF + llama.cpp
```

Use a downloaded Transformers model directory:

```python
from scvp import Message, Role, SCVPModel

model = SCVPModel(
  provider="local",
  model_path="./models/my-model",
  device="auto",
  max_tokens=256,
)
response = model.chat([Message(role=Role.USER, content="اكتب ملخصًا قصيرًا للمشروع.")])
print(response.content)
```

Or use a local GGUF file:

```python
model = SCVPModel(provider="local", model_path="./models/model.gguf")
```

The model is loaded lazily from the local path. No API key or network request
is made by the provider. `mock` and `local_project` remain test/demo providers;
they are not presented as real intelligence.

## Architecture

```mermaid
flowchart TB
    App[Your Application] --> SDK[SCVP SDK]
    SDK --> Core[SCVP Core]
    Core --> Runtime["Agent Runtime (phase 3)"]
    Runtime --> MTS["Model / Tools / Memory / Search (phases 2, 4, 5, 6)"]
    MTS --> Providers[(Providers / Adapters)]
    Core -.->|Registry pattern| Providers
```

Every layer only depends on the interfaces below it, never on a concrete
provider. `scvp.core.registry.Registry` is the one mechanism every
swappable layer (models today; tools, search, memory in later phases)
uses to register and resolve a named provider — Core never imports
`OpenAIProvider` or `RedisMemory` directly.

## Repository layout

```
scvp/
├── core/                    # config, logging, exceptions, registry, shared types
├── models/                  # ModelProvider interface, SCVPModel, MockModelProvider
│   └── providers/mock.py
├── agents/                  # Agent, planner, executor, and sequential runtime
├── tools/                   # Injectable SCVPTool contract and ToolResult
└── cli/                     # `scvp` command (init, model, agent/tool/plugin stubs)
    └── templates/minimal/   # `scvp init` starter template
tests/                       # pytest suite for everything above
examples/quickstart.py       # runnable end-to-end example
```

Each layer is an independent, replaceable module under `scvp/`, with optional
providers selected through registries or dependency injection.

## Install

```bash
cd scvp
pip install -e ".[dev]"
```

Published package links:

- Python: [PyPI](https://pypi.org/project/scvp/)
- JavaScript: [npm](https://www.npmjs.com/package/@sovereignempirex/scvp)
- Source: [GitHub](https://github.com/sovereignempirex-ux/svcp)

The JavaScript Phase 5 package is published separately because the runtime is
currently implemented in Python. See [javascript/README.md](javascript/README.md)
for installation and usage.

## Quickstart

```python
from scvp import Message, Role, SCVPModel

model = SCVPModel(provider="mock")
response = model.chat([Message(role=Role.USER, content="Hello, SCVP!")])
print(response.content)
```

Or scaffold a starter project with the CLI:

```bash
scvp init my-agent
cd my-agent
python main.py
```

The CLI also exposes the implemented runtime:

```bash
scvp model list
scvp search
scvp plugin list
scvp agent run "Explain SCVP"
scvp config --key model.provider
scvp serve --host 127.0.0.1 --port 8765
scvp test
```

Run a provider-agnostic agent with the built-in mock model:

```python
from scvp import Agent

agent = Agent(name="support")
result = agent.run("Explain what SCVP is.")
print(result.content)
```

The current Agent Runtime is intentionally sequential. It supports injected
tools, custom planners, explicit step limits, and typed execution state.
Multi-agent orchestration and parallel execution are later phases.

### Tools

Tools can be registered and invoked through `ToolRegistry`. `FunctionTool`
adapts a regular Python callable, while tool schemas validate required fields
and basic JSON types before execution. Registries also enforce declared
permissions and optional timeouts.

```python
from scvp import FunctionTool, ToolRegistry

tools = ToolRegistry([
  FunctionTool(
    "greet",
    lambda arguments: "Hello, " + arguments["name"],
    schema={
      "required": ["name"],
      "properties": {"name": {"type": "string"}},
    },
  )
])
result = tools.invoke("greet", {"name": "SCVP"})
```

### Memory

Phase 5 provides a provider-agnostic conversation memory interface and a
deterministic in-process backend:

```python
from scvp import Agent, InMemoryProvider, SCVPModel

memory = InMemoryProvider()
agent = Agent(model=SCVPModel("mock"), memory=memory)
agent.run("Remember that my name is Sam.", conversation_id="support-1")
history = memory.load("support-1")
```

Pass another `MemoryProvider` implementation to `Agent` to use a persistent
backend. Memory is opt-in; agents without a memory provider retain their
existing behavior.

### Search

Phase 6 provides a provider-agnostic full-text search interface and a
deterministic in-process backend:

```python
from scvp import InMemorySearchProvider, SearchDocument

search = InMemorySearchProvider()
search.index(SearchDocument("guide", "SCVP agents use tools and memory."))
results = search.search("agents memory")
print(results[0].document.id, results[0].score)
```

Search providers are replaceable through `search_registry`, so a persistent
or vector-backed implementation can be added without changing application code.

For real web search, use Google's Custom Search JSON API. Create a Programmable
Search Engine, enable the Custom Search JSON API, and set credentials as
environment variables:

```bash
set SCVP_SEARCH__GOOGLE__API_KEY=your-google-api-key
set SCVP_SEARCH__GOOGLE__CX=your-search-engine-id
```

```python
from scvp import GoogleSearchProvider

search = GoogleSearchProvider()
results = search.search("Python agent runtime", limit=5)
for result in results:
  print(result.document.metadata["title"], result.document.id)
```

Google credentials are never read from config files or committed to source.

### RAG / Knowledge

Phase 7 adds a provider-agnostic knowledge base. It chunks source documents,
indexes them through any local or persistent `SearchProvider`, and formats
retrieved context for a model prompt. Without an embedder it uses explicit
lexical fallback; for real semantic retrieval install the optional embedding
backend:

```python
from scvp import KnowledgeBase

knowledge = KnowledgeBase()
knowledge.ingest("handbook", "SCVP stores knowledge as searchable chunks.")
context = knowledge.build_context("How does SCVP store knowledge?")
print(context)
```

Real semantic RAG with `sentence-transformers`:

```bash
pip install "scvp[embeddings]"
```

```python
from scvp import KnowledgeBase, SentenceTransformerEmbedder

knowledge = KnowledgeBase(embedder=SentenceTransformerEmbedder())
knowledge.ingest("handbook", "SCVP stores knowledge as searchable chunks.")
context = knowledge.build_context("Where is SCVP knowledge stored?")
```

The embedding model is downloaded and loaded by `sentence-transformers` on
first use. The default mock model is not used for semantic retrieval because
its embeddings are intentionally pseudo-random for tests only.

### HTTP API

Phase 8 exposes the real providers through an optional FastAPI service:

```bash
pip install "scvp[api]"
uvicorn scvp.api:create_app --factory --reload
```

The service provides `GET /health`, `POST /knowledge/documents`,
`POST /knowledge/search`, `POST /search`, and `POST /agents/run`. OpenAPI
documentation is available at `/docs`. Inject `GoogleSearchProvider`, a
semantic `KnowledgeBase`, and an `Agent` into `create_app()` when embedding
the service in your own server.

For a production API system with PostgreSQL-backed API keys, usage tracking,
and rate limiting:

```bash
pip install "scvp[api-security]"
set SCVP_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/scvp
set SCVP_ADMIN_TOKEN=replace-with-a-long-secret
```

```python
import os
from scvp.api import APISecurity, create_app

security = APISecurity(os.environ["SCVP_DATABASE_URL"], rate_limit_per_minute=120)
app = create_app(security=security, admin_token=os.environ["SCVP_ADMIN_TOKEN"])
```

Use `POST /admin/api-keys` with `X-Admin-Token` to create a key. Clients send
that key as `X-API-Key`. The raw key is returned only at creation time; only
its SHA-256 hash is stored. `GET /admin/usage` shows request counts, and
excess requests receive HTTP 429 with a `Retry-After` header.

### Content Moderation

The API blocks harmful and explicit 18+ input before indexing, searching, or
running an agent. The default policy records actor IDs and timestamps, never
the violating text:

- explicit sexual content is blocked;
- severe self-harm, violent, or illegal instructions cause a permanent ban;
- repeated violations cause a temporary ban;
- admins can clear a ban with `POST /admin/moderation/unban` and
  `X-Admin-Token`.

Pass a custom `ModerationService` to `create_app()` to replace the detector or
connect ban records to a persistent moderation store in production.

Use `KnowledgeBase(search=your_search_provider)` to connect another indexed
backend. Web search providers such as Google are for external search and do
not replace document indexing providers.

Run the full walkthrough (chat, stream, embed, classify):

```bash
python examples/quickstart.py
```

## Configuration

Put a `scvp.config.yaml` (or `.json`) in your project root. It's
overridable by `SCVP_`-prefixed environment variables (`__` = nesting):

```yaml
model:
  provider: mock
```

```bash
export SCVP_MODEL__PROVIDER=mock   # overrides model.provider
```

Secrets (API keys, etc.) are **never** read from the config file — only
from environment variables (see `.env.example`) — so `scvp.config.yaml`
is always safe to commit.

## Run the tests

```bash
pytest
```

## Roadmap

- [x] Phase 0 — Architecture
- [x] Phase 1 — Core (config, logging, exceptions, registry, types)
- [x] Phase 2 — Model Interface (`ModelProvider`, `SCVPModel`, Mock provider) — *started*
- [x] Phase 3 — Agent Runtime (sequential MVP)
- [x] Phase 4 — Tool System
- [x] Phase 5 — Memory (provider interface and in-memory backend)
- [x] Phase 6 — Search (provider interface and in-memory full-text backend)
- [x] Phase 7 — RAG / Knowledge (chunking, ingestion, retrieval, context builder)
- [x] Phase 8 — API (FastAPI service for knowledge, search, and agents)
- [x] Phase 9 — Plugins (entry-point discovery and lifecycle manager)
- [x] Phase 10 — SDK (Python and JavaScript API clients)
- [x] Phase 11 — CLI (runtime, providers, plugins, API server, and tests)
- [x] Phase 12 — Testing (integration/security suites and CI matrix)
- [x] Phase 13 — Documentation (guides, operations, testing, and publishing)

## Design principles

- **No provider lock-in.** Core never imports a concrete vendor SDK.
- **Real over fake.** No empty stub files — every file in this repo runs
  and is covered by a test.
- **Secrets stay in the environment**, never in source or config files.
- **Fail loud.** Missing config, unregistered providers, and unsupported
  capabilities raise a specific, typed exception instead of a silent
  no-op.

## License

MIT — see `LICENSE`.
