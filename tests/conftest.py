import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest


def page(records: list[dict[str, Any]] | None, page: int = 1, pages: int = 1) -> list:
    """Build a World Bank API response body for one page."""
    total = len(records or [])
    return [
        {"page": page, "pages": pages, "per_page": 1000, "total": total},
        records,
    ]


def api_error(code: str = "120", value: str = "Invalid value") -> list:
    """Build a World Bank API error message body."""
    return [{"message": [{"id": code, "key": "Error", "value": value}]}]


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


@dataclass
class Request:
    url: str
    path: str
    query: dict[str, str]
    headers: dict[str, str]


@dataclass
class MockApi:
    """Route requests to canned responses keyed by the path after `/v2/`."""

    routes: dict[str, Any] = field(default_factory=dict)
    requests: list[Request] = field(default_factory=list)

    def add(self, path: str, response: Any) -> None:
        """Register a response: a JSON body, raw bytes, an exception, or a
        callable that receives the `Request` and returns one of those."""
        self.routes[path] = response

    def urlopen(self, request: urllib.request.Request, timeout: float | None = None):
        parsed = urlparse(request.full_url)
        path = parsed.path.removeprefix("/v2/")
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        headers = {k.lower(): v for k, v in request.header_items()}
        recorded = Request(request.full_url, path, query, headers)
        self.requests.append(recorded)

        if path not in self.routes:
            raise AssertionError(f"Unexpected request to {request.full_url}")
        response = self.routes[path]
        if isinstance(response, Callable) and not isinstance(response, type):
            response = response(recorded)
        if isinstance(response, BaseException):
            raise response
        if isinstance(response, bytes):
            return FakeResponse(response)
        return FakeResponse(json.dumps(response).encode())


@pytest.fixture
def mock_api(monkeypatch: pytest.MonkeyPatch) -> MockApi:
    api = MockApi()
    monkeypatch.setattr(urllib.request, "urlopen", api.urlopen)
    return api


def http_error(url: str, code: int, body: bytes) -> urllib.error.HTTPError:
    import io

    return urllib.error.HTTPError(url, code, "Error", {}, io.BytesIO(body))
