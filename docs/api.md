# HTTP API and Security

## Start the API

```bash
python -m pip install -e ".[api]"
uvicorn scvp.api:create_app --factory --host 127.0.0.1 --port 8765
```

OpenAPI is available at `http://127.0.0.1:8765/docs`.

Endpoints:

- `GET /health`
- `POST /knowledge/documents`
- `POST /knowledge/search`
- `POST /search`
- `POST /agents/run`

## PostgreSQL API keys

```bash
python -m pip install -e ".[api-security]"
```

Set `SCVP_DATABASE_URL` and `SCVP_ADMIN_TOKEN` before starting the server. Create a key with `POST /admin/api-keys` and `X-Admin-Token`, then send it as `X-API-Key`. Only a SHA-256 hash is stored.

Usage is available at `GET /admin/usage`. Revocation is available at `POST /admin/api-keys/revoke`. Rate-limit responses return HTTP 429 with `Retry-After`.

## Moderation

The API checks document content, search queries, and agent goals before processing. Harmful or explicit content is rejected. Repeated violations produce a temporary ban; severe categories produce a permanent ban. Admins can call `POST /admin/moderation/unban?actor_id=...`.

For production, inject a moderation service backed by durable storage so bans survive process restarts.
