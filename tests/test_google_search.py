import io
import json
from unittest.mock import patch

from scvp import GoogleSearchProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_google_search_normalizes_api_results():
    payload = {
        "items": [
            {
                "title": "SCVP",
                "link": "https://example.com/scvp",
                "displayLink": "example.com",
                "snippet": "A provider agnostic runtime.",
            }
        ]
    }
    provider = GoogleSearchProvider(api_key="key", cx="engine")

    with patch("scvp.search.providers.google.urlopen", return_value=FakeResponse(payload)) as open_url:
        results = provider.search("SCVP", limit=1, offset=2)

    request = open_url.call_args.args[0]
    assert "start=3" in request.full_url
    assert results[0].document.id == "https://example.com/scvp"
    assert results[0].document.metadata["title"] == "SCVP"


def test_google_provider_does_not_index_local_documents():
    provider = GoogleSearchProvider(api_key="key", cx="engine")

    try:
        provider.index(None)
    except NotImplementedError as exc:
        assert "does not index" in str(exc)
    else:
        raise AssertionError("Expected Google provider to reject local indexing")