"""Google Custom Search JSON API provider."""

from __future__ import annotations

import json
import os
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scvp.core.exceptions import ConfigError, SearchError
from scvp.search.base import SearchDocument, SearchProvider, SearchResult


class GoogleSearchProvider(SearchProvider):
    """Search the public web through Google's Custom Search JSON API.

    Create a Programmable Search Engine and enable the Custom Search JSON API.
    Credentials are read from ``SCVP_SEARCH__GOOGLE__API_KEY`` and
    ``SCVP_SEARCH__GOOGLE__CX`` unless passed explicitly.
    """

    endpoint = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cx: Optional[str] = None,
        timeout: float = 10.0,
        user_agent: str = "scvp/0.1",
    ):
        self.api_key = api_key or os.getenv("SCVP_SEARCH__GOOGLE__API_KEY")
        self.cx = cx or os.getenv("SCVP_SEARCH__GOOGLE__CX")
        self.timeout = timeout
        self.user_agent = user_agent
        if not self.api_key:
            raise ConfigError(
                "Google Search requires SCVP_SEARCH__GOOGLE__API_KEY."
            )
        if not self.cx:
            raise ConfigError("Google Search requires SCVP_SEARCH__GOOGLE__CX.")

    def index(self, document: SearchDocument) -> None:
        raise NotImplementedError(
            "GoogleSearchProvider searches the web and does not index local documents."
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            return []
        if not isinstance(limit, int) or not 1 <= limit <= 10:
            raise ValueError("Google Search limit must be between 1 and 10.")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be zero or greater.")

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": limit,
            "start": offset + 1,
        }
        request = Request(
            f"{self.endpoint}?{urlencode(params)}",
            headers={"User-Agent": self.user_agent},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = self._error_detail(exc)
            raise SearchError(f"Google Search request failed ({exc.code}): {detail}") from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise SearchError(f"Google Search request failed: {exc}") from exc

        return [
            SearchResult(
                document=SearchDocument(
                    id=item["link"],
                    content=item.get("snippet", ""),
                    metadata={
                        "title": item.get("title", ""),
                        "link": item["link"],
                        "display_link": item.get("displayLink", ""),
                    },
                ),
                score=float(offset + index + 1),
            )
            for index, item in enumerate(payload.get("items", []))
            if item.get("link")
        ]

    def delete(self, document_id: str) -> None:
        raise NotImplementedError(
            "GoogleSearchProvider searches the web and has no local documents to delete."
        )

    def clear(self) -> None:
        raise NotImplementedError(
            "GoogleSearchProvider searches the web and has no local index to clear."
        )

    @staticmethod
    def _error_detail(error: HTTPError) -> str:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            return payload.get("error", {}).get("message", str(error))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return str(error)


GoogleSearch = GoogleSearchProvider