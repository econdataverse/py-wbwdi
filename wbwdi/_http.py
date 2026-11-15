"""Internal helpers for talking to the World Bank API."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://api.worldbank.org/v2/"
USER_AGENT = "wbwdi Python library (https://github.com/econdataverse/py-wbwdi)"
ERROR_DOCS = (
    "Read more at <https://datahelpdesk.worldbank.org/"
    "knowledgebase/articles/898620-api-error-codes>"
)


def perform_request(
    resource: str,
    language: str | None = None,
    per_page: int = 1000,
    date: str | None = None,
    most_recent_only: bool = False,
    source: int | str | None = None,
    progress: bool = False,
    base_url: str = BASE_URL,
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    """Request a World Bank API resource and return all records across pages.

    Parameters
    ----------
    resource
        API endpoint, e.g. ``"incomeLevels"`` or ``"country/US/indicator/SP.POP.TOTL"``.
    language
        Language code for the response. If ``None``, the API default is used.
    per_page
        Number of records per page. Must be between 1 and 32,500.
    date
        Date range such as ``"2000:2020"``. If ``None``, no date filter is applied.
    most_recent_only
        Whether to request only the most recent value (``mrv=1``).
    source
        Data source ID. If ``None``, the API default is used.
    progress
        Whether to print page progress to stderr for paginated responses.
    base_url
        Base URL of the World Bank API.
    timeout
        Timeout in seconds for each HTTP request.

    Returns
    -------
    list[dict[str, Any]]
        The records of all pages combined. Empty if the API returns no data.

    Raises
    ------
    ValueError
        If `per_page` is not an integer between 1 and 32,500.
    RuntimeError
        If the request fails or the API returns an error message.
    """
    validate_per_page(per_page)

    url = create_request_url(
        base_url, resource, language, per_page, date, most_recent_only, source
    )

    metadata, records = get_page(url, timeout)
    pages = int(metadata.get("pages") or 1)

    for page in range(2, pages + 1):
        if progress:
            print_progress(page, pages)
        _, page_records = get_page(f"{url}&page={page}", timeout)
        records.extend(page_records)

    if progress and pages > 1:
        print(file=sys.stderr)

    return records


def validate_per_page(per_page: int) -> None:
    if (
        not isinstance(per_page, int)
        or isinstance(per_page, bool)
        or not (1 <= per_page <= 32500)
    ):
        raise ValueError("`per_page` must be an integer between 1 and 32,500.")


def create_request_url(
    base_url: str,
    resource: str,
    language: str | None,
    per_page: int,
    date: str | None,
    most_recent_only: bool,
    source: int | str | None,
) -> str:
    prefix = f"{base_url}{language}/" if language else base_url
    params: dict[str, Any] = {"format": "json", "per_page": per_page}
    if most_recent_only:
        params["mrv"] = 1
    if date:
        params["date"] = date
    if source is not None:
        params["source"] = source
    return f"{prefix}{resource}?{urllib.parse.urlencode(params, safe=':')}"


def get_page(url: str, timeout: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fetch one page and split it into its metadata and records."""
    body = get_json(url, timeout)
    raise_for_api_error(body)
    if not isinstance(body, list) or len(body) < 2:
        raise RuntimeError(f"Unexpected response format from {url}")
    return body[0] or {}, list(body[1] or [])


def get_json(url: str, timeout: float) -> Any:
    """Perform a GET request and parse the JSON response body.

    API error messages in a JSON body are surfaced even when the HTTP status
    signals an error.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as e:
        body = parse_json(e.read())
        raise_for_api_error(body)
        raise RuntimeError(
            f"Request to {url} failed with HTTP status {e.code}: {e.reason}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Request to {url} failed: {e.reason}") from e

    body = parse_json(raw)
    if body is None:
        raise RuntimeError(f"Failed to parse JSON response from {url}")
    return body


def parse_json(raw: bytes) -> Any:
    """Parse a JSON body, returning ``None`` if it is not valid JSON."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def raise_for_api_error(body: Any) -> None:
    """Raise a `RuntimeError` if `body` is a World Bank API error message."""
    if not (
        isinstance(body, list)
        and len(body) >= 1
        and isinstance(body[0], dict)
        and "message" in body[0]
    ):
        return
    messages = body[0]["message"] or [{}]
    message = messages[0]
    raise RuntimeError(
        "\n".join(
            [
                f"Error code: {message.get('id', 'unknown')}",
                message.get("value", "Unknown API error."),
                ERROR_DOCS,
            ]
        )
    )


def print_progress(current: int, total: int) -> None:
    print(f"Progress: {current}/{total}", end="\r", file=sys.stderr)
