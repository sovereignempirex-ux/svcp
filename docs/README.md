# SCVP Documentation

SCVP is a provider-agnostic runtime for local AI agents, tools, memory, search, RAG, HTTP APIs, plugins, and SDK clients.

## Guides

- [Getting started](getting-started.md)
- [Local AI](local-ai.md)
- [RAG and search](rag.md)
- [API and security](api.md)
- [Plugins and SDKs](plugins-sdk.md)
- [Testing and publishing](testing-publishing.md)

## Design rules

1. Providers are selected through registries or injected interfaces.
2. Secrets are read from environment variables, never committed to config.
3. The `mock` provider is for tests; `local` runs a model from disk.
4. Optional dependencies stay optional until a feature is used.
5. API moderation should run before indexing, search, or agent execution.

For the complete phase history and examples, see the [root README](../README.md).
