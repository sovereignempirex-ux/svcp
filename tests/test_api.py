import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from scvp import KnowledgeBase
from scvp.api import create_app


@pytest.mark.integration
def test_api_health_and_knowledge_endpoints():
    client = TestClient(create_app(knowledge=KnowledgeBase()))

    assert client.get("/health").json() == {"status": "ok", "service": "scvp"}
    ingest = client.post(
        "/knowledge/documents",
        json={"id": "guide", "content": "SCVP uses searchable memory."},
    )
    assert ingest.status_code == 200
    assert ingest.json()["chunks_indexed"] == 1

    results = client.post("/knowledge/search", json={"query": "memory"})
    assert results.status_code == 200
    assert results.json()["results"][0]["document_id"] == "guide"


@pytest.mark.integration
def test_api_reports_missing_providers():
    client = TestClient(create_app())

    assert client.post("/search", json={"query": "web"}).status_code == 503
    assert client.post("/agents/run", json={"goal": "hello"}).status_code == 503


@pytest.mark.integration
def test_api_blocks_adult_content():
    client = TestClient(create_app(knowledge=KnowledgeBase()))
    response = client.post(
        "/knowledge/documents",
        json={"id": "blocked", "content": "explicit porn content"},
    )
    assert response.status_code == 403