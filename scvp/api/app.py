"""FastAPI application factory for SCVP services."""

import os
import hashlib
from typing import Any, Dict, Optional

from scvp.agents import Agent
from scvp.knowledge import KnowledgeBase
from scvp.search import SearchProvider
from scvp.api.security import APIKeyError, APISecurity, RateLimitError
from scvp.moderation import BanStatus, ModerationService


def create_app(
    knowledge: Optional[KnowledgeBase] = None,
    search: Optional[SearchProvider] = None,
    agent: Optional[Agent] = None,
    security: Optional[APISecurity] = None,
    admin_token: Optional[str] = None,
    moderation: Optional[ModerationService] = None,
):
    """Create the SCVP API with injectable real providers.

    FastAPI is optional so the core SDK remains dependency-light. Install API
    support with ``pip install 'scvp[api]'``.
    """
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException, Request
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError(
            "Install SCVP API support with: pip install 'scvp[api]'"
        ) from exc

    class HealthResponse(BaseModel):
        status: str
        service: str

    class DocumentRequest(BaseModel):
        id: str = Field(min_length=1)
        content: str = Field(min_length=1)
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class SearchRequest(BaseModel):
        query: str = Field(min_length=1)
        limit: int = Field(default=5, ge=1, le=10)
        offset: int = Field(default=0, ge=0)

    class AgentRequest(BaseModel):
        goal: str = Field(min_length=1)
        conversation_id: Optional[str] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class APIKeyRequest(BaseModel):
        name: str = Field(min_length=1, max_length=120)

    class RevokeKeyRequest(BaseModel):
        key_id: int = Field(ge=1)

    app = FastAPI(
        title="SCVP API",
        version="0.1.0",
        description="Provider-agnostic agent, search, and RAG API.",
    )
    if security is None and os.getenv("SCVP_DATABASE_URL"):
        security = APISecurity(os.environ["SCVP_DATABASE_URL"])
        admin_token = admin_token or os.getenv("SCVP_ADMIN_TOKEN")
    knowledge_base = knowledge or KnowledgeBase()
    moderation_service = moderation or ModerationService()

    def require_api_key(request: Request, api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
        if security is None:
            return
        try:
            security.authorize(api_key, request.url.path)
        except APIKeyError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except RateLimitError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": str(exc.retry_after)},
            ) from exc

    def require_admin(token: Optional[str] = Header(default=None, alias="X-Admin-Token")) -> None:
        if not APISecurity.valid_admin_token(token, admin_token):
            raise HTTPException(status_code=403, detail="Admin token is invalid.")

    def check_content(actor_id: str, text: str) -> None:
        decision = moderation_service.moderate(actor_id, text)
        if not decision.allowed:
            status_code = 403 if decision.ban_status == BanStatus.NONE else 423
            raise HTTPException(
                status_code=status_code,
                detail={"error": "content_blocked", "reason": decision.reason, "ban_status": decision.ban_status.value},
            )

    @staticmethod
    def actor_id(api_key: Optional[str], request: Request) -> str:
        if api_key:
            return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        return f"anonymous:{request.client.host if request.client else 'unknown'}"

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="scvp")

    @app.post("/knowledge/documents", dependencies=[Depends(require_api_key)])
    def ingest_document(request: DocumentRequest, http_request: Request, api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
        check_content(actor_id(api_key, http_request), request.content)
        chunks = knowledge_base.ingest(request.id, request.content, request.metadata)
        return {"document_id": request.id, "chunks_indexed": chunks}

    @app.post("/knowledge/search", dependencies=[Depends(require_api_key)])
    def search_knowledge(request: SearchRequest, http_request: Request, api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
        check_content(actor_id(api_key, http_request), request.query)
        results = knowledge_base.retrieve(request.query, limit=request.limit)
        return {
            "query": request.query,
            "results": [
                {
                    "document_id": result.document_id,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata,
                }
                for result in results
            ],
        }

    @app.post("/search", dependencies=[Depends(require_api_key)])
    def search_web(request: SearchRequest, http_request: Request, api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
        check_content(actor_id(api_key, http_request), request.query)
        if search is None:
            raise HTTPException(status_code=503, detail="No web search provider configured.")
        try:
            results = search.search(request.query, request.limit, request.offset)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Search provider request failed.") from exc
        return {
            "query": request.query,
            "results": [
                {
                    "id": result.document.id,
                    "content": result.document.content,
                    "score": result.score,
                    "metadata": result.document.metadata,
                }
                for result in results
            ],
        }

    @app.post("/agents/run", dependencies=[Depends(require_api_key)])
    def run_agent(request: AgentRequest, http_request: Request, api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
        check_content(actor_id(api_key, http_request), request.goal)
        if agent is None:
            raise HTTPException(status_code=503, detail="No agent configured.")
        try:
            result = agent.run(
                request.goal,
                metadata=request.metadata,
                conversation_id=request.conversation_id,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Agent execution failed.") from exc
        return {
            "content": result.content,
            "status": result.status.value,
            "steps": result.state.step,
        }

    @app.post("/admin/api-keys", dependencies=[Depends(require_admin)])
    def create_api_key(request: APIKeyRequest) -> Dict[str, str]:
        if security is None:
            raise HTTPException(status_code=503, detail="API security is not configured.")
        return {"name": request.name, "api_key": security.create_key(request.name)}

    @app.get("/admin/usage", dependencies=[Depends(require_admin)])
    def api_usage() -> Dict[str, Any]:
        if security is None:
            raise HTTPException(status_code=503, detail="API security is not configured.")
        return security.usage()

    @app.post("/admin/api-keys/revoke", dependencies=[Depends(require_admin)])
    def revoke_api_key(request: RevokeKeyRequest) -> Dict[str, Any]:
        if security is None:
            raise HTTPException(status_code=503, detail="API security is not configured.")
        revoked = security.revoke(request.key_id)
        if not revoked:
            raise HTTPException(status_code=404, detail="API key not found.")
        return {"revoked": True, "key_id": request.key_id}

    @app.post("/admin/moderation/unban", dependencies=[Depends(require_admin)])
    def unban_actor(actor_id: str) -> Dict[str, Any]:
        return {"actor_id": actor_id, "unbanned": moderation_service.unban(actor_id)}

    return app