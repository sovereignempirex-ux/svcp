# Testing and Publishing

## Test locally

```bash
python -m pytest -q --strict-markers
python -m pytest -q -m integration
python -m pytest -q -m security
```

The test suite covers providers, agent runtime, memory, search, RAG, API, SDK, plugins, and security behavior.

## Build distributions

```bash
python -m build --sdist --wheel
```

The Python package is published by the release workflow. The JavaScript package is in `javascript/` and is published separately to npm.

## Release checklist

1. Run the full strict test suite.
2. Build the wheel and source distribution.
3. Create a GitHub Release tag.
4. Configure `PYPI_API_TOKEN` and `NPM_TOKEN` repository secrets.
5. Confirm the published package metadata and README links.
6. Never commit API keys, model weights, database passwords, or admin tokens.
