import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient

from scvp import KnowledgeBase
from scvp.api import APISecurity, create_app


@pytest.mark.integration
@pytest.mark.security
def test_api_keys_protect_routes_and_rate_limit(tmp_path):
    security = APISecurity(f"sqlite:///{tmp_path / 'api.db'}", rate_limit_per_minute=1)
    api_key = security.create_key("integration-test")
    client = TestClient(
        create_app(
            knowledge=KnowledgeBase(),
            security=security,
            admin_token="admin-secret",
        )
    )

    assert client.post(
        "/knowledge/search", json={"query": "memory"}
    ).status_code == 401
    first = client.post(
        "/knowledge/search",
        json={"query": "memory"},
        headers={"X-API-Key": api_key},
    )
    assert first.status_code == 200
    limited = client.post(
        "/knowledge/search",
        json={"query": "memory"},
        headers={"X-API-Key": api_key},
    )
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"


@pytest.mark.integration
@pytest.mark.security
def test_admin_can_create_and_view_keys(tmp_path):
    security = APISecurity(f"sqlite:///{tmp_path / 'api.db'}")
    client = TestClient(create_app(security=security, admin_token="admin-secret"))

    created = client.post(
        "/admin/api-keys",
        json={"name": "dashboard"},
        headers={"X-Admin-Token": "admin-secret"},
    )
    assert created.status_code == 200
    assert created.json()["api_key"].startswith("scvp_")

    usage = client.get("/admin/usage", headers={"X-Admin-Token": "admin-secret"})
    assert usage.status_code == 200
    assert usage.json()["keys"][0]["name"] == "dashboard"