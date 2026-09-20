import json
from unittest.mock import patch

from scvp import SCVPClient, SCVPAPIError


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload

    def close(self):
        pass


def test_python_sdk_calls_api_and_sends_api_key():
    client = SCVPClient("http://api.test", api_key="scvp_key")
    with patch("scvp.sdk.client.urlopen", return_value=FakeResponse({"status": "ok"})) as open_url:
        assert client.health() == {"status": "ok"}
    request = open_url.call_args.args[0]
    assert request.full_url == "http://api.test/health"
    assert request.get_header("X-api-key") == "scvp_key"


def test_python_sdk_maps_http_errors():
    client = SCVPClient()
    error = __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(
        "http://api.test/health", 401, "Unauthorized", {}, FakeResponse({"detail": "Invalid API key."})
    )
    with patch("scvp.sdk.client.urlopen", side_effect=error):
        try:
            client.health()
        except SCVPAPIError as exc:
            assert exc.status == 401
            assert "Invalid API key" in exc.detail
        else:
            raise AssertionError("Expected SCVPAPIError")