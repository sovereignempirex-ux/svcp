import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient

from scvp.api import APISecurity, create_app


@pytest.mark.security
def test_api_key_is_never_stored_in_plaintext(tmp_path):
    security = APISecurity(f"sqlite:///{tmp_path / 'security.db'}")
    raw_key = security.create_key("secret-client")

    with security._Session(security._engine) as session:
        stored = session.query(security._APIKey).one()

    assert raw_key not in stored.key_hash
    assert len(stored.key_hash) == 64


@pytest.mark.security
def test_wrong_admin_token_and_revoked_key_are_rejected(tmp_path):
    security = APISecurity(f"sqlite:///{tmp_path / 'security.db'}")
    client = TestClient(create_app(security=security, admin_token="correct"))

    forbidden = client.post(
        "/admin/api-keys",
        json={"name": "client"},
        headers={"X-Admin-Token": "wrong"},
    )
    assert forbidden.status_code == 403

    raw_key = security.create_key("client")
    with security._Session(security._engine) as session:
        key_id = session.query(security._APIKey).one().id
    assert security.revoke(key_id) is True
    assert client.post(
        "/knowledge/search",
        json={"query": "anything"},
        headers={"X-API-Key": raw_key},
    ).status_code == 401


@pytest.mark.security
def test_api_rejects_invalid_payloads(tmp_path):
    security = APISecurity(f"sqlite:///{tmp_path / 'security.db'}")
    raw_key = security.create_key("client")
    client = TestClient(create_app(security=security))

    response = client.post(
        "/knowledge/documents",
        json={"id": "", "content": ""},
        headers={"X-API-Key": raw_key},
    )
    assert response.status_code == 422