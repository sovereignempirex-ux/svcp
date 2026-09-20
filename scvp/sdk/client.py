"""Dependency-free Python client for the SCVP HTTP API."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SCVPAPIError(RuntimeError):
    """Raised when the SCVP API returns an error or cannot be reached."""

    def __init__(self, status: Optional[int], detail: str):
        super().__init__(f"SCVP API error{f' ({status})' if status else ''}: {detail}")
        self.status = status
        self.detail = detail


class SCVPClient:
    """Small synchronous client for health, RAG, search, and agent endpoints."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765", api_key: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def ingest(self, document_id: str, content: str, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return self._request("POST", "/knowledge/documents", {"id": document_id, "content": content, "metadata": dict(metadata or {})})

    def knowledge_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        return self._request("POST", "/knowledge/search", {"query": query, "limit": limit})

    def web_search(self, query: str, limit: int = 5, offset: int = 0) -> Dict[str, Any]:
        return self._request("POST", "/search", {"query": query, "limit": limit, "offset": offset})

    def run_agent(self, goal: str, conversation_id: Optional[str] = None, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return self._request("POST", "/agents/run", {"goal": goal, "conversation_id": conversation_id, "metadata": dict(metadata or {})})

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
                detail = payload.get("detail", str(exc))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                detail = str(exc)
            raise SCVPAPIError(exc.code, str(detail)) from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise SCVPAPIError(None, str(exc)) from exc