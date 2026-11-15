import json
import urllib.error

import pytest

from wbwdi._http import (
    USER_AGENT,
    create_request_url,
    perform_request,
    validate_per_page,
)

from .conftest import api_error, http_error, page


def test_create_request_url_with_all_parameters():
    url = create_request_url(
        "https://api.worldbank.org/v2/",
        "incomeLevels",
        "en",
        1000,
        "2020:2022",
        True,
        2,
    )
    assert url == (
        "https://api.worldbank.org/v2/en/incomeLevels"
        "?format=json&per_page=1000&mrv=1&date=2020:2022&source=2"
    )


def test_create_request_url_without_optional_parameters():
    url = create_request_url(
        "https://api.worldbank.org/v2/", "languages", None, 50, None, False, None
    )
    assert url == "https://api.worldbank.org/v2/languages?format=json&per_page=50"


@pytest.mark.parametrize("per_page", [1, 1000, 32500])
def test_validate_per_page_valid(per_page):
    validate_per_page(per_page)


@pytest.mark.parametrize("per_page", [0, 32501, "1000", 1.5, True, None])
def test_validate_per_page_invalid(per_page):
    with pytest.raises(ValueError, match="`per_page` must be an integer"):
        validate_per_page(per_page)


def test_single_page(mock_api):
    mock_api.add("incomeLevels", page([{"id": "HIC"}, {"id": "LIC"}]))

    result = perform_request("incomeLevels")

    assert [r["id"] for r in result] == ["HIC", "LIC"]
    assert len(mock_api.requests) == 1
    assert mock_api.requests[0].headers["user-agent"] == USER_AGENT


def test_pagination_requests_each_page_once_with_user_agent(mock_api):
    def respond(request):
        number = int(request.query.get("page", 1))
        return page([{"id": f"record-{number}"}], page=number, pages=3)

    mock_api.add("languages", respond)

    result = perform_request("languages", per_page=1)

    assert [r["id"] for r in result] == ["record-1", "record-2", "record-3"]
    assert [r.query.get("page") for r in mock_api.requests] == [None, "2", "3"]
    assert all(r.headers["user-agent"] == USER_AGENT for r in mock_api.requests)


def test_pagination_with_string_metadata(mock_api):
    def respond(request):
        number = request.query.get("page", "1")
        return [{"page": number, "pages": "2"}, [{"id": number}]]

    mock_api.add("languages", respond)

    assert [r["id"] for r in perform_request("languages")] == ["1", "2"]


def test_progress_is_printed_to_stderr(mock_api, capsys):
    mock_api.add(
        "languages",
        lambda r: page([{}], page=int(r.query.get("page", 1)), pages=2),
    )

    perform_request("languages", progress=True)

    captured = capsys.readouterr()
    assert "Progress: 2/2" in captured.err
    assert captured.out == ""


def test_empty_result(mock_api):
    mock_api.add("country/US/indicator/X", [{"page": 1, "pages": 0}, None])
    assert perform_request("country/US/indicator/X") == []


def test_api_error_message(mock_api):
    mock_api.add(
        "invalid", api_error("120", "The provided parameter value is not valid")
    )

    with pytest.raises(RuntimeError) as excinfo:
        perform_request("invalid")

    message = str(excinfo.value)
    assert "Error code: 120" in message
    assert "The provided parameter value is not valid" in message
    assert "api-error-codes" in message


def test_http_error_with_json_body(mock_api):
    body = json.dumps(api_error("150", "Unsupported language")).encode()
    mock_api.add("xx/topics", lambda r: http_error(r.url, 400, body))

    with pytest.raises(RuntimeError, match="Error code: 150"):
        perform_request("topics", language="xx")


def test_http_error_with_html_body(mock_api):
    mock_api.add(
        "topics", lambda r: http_error(r.url, 502, b"<html>Bad gateway</html>")
    )

    with pytest.raises(RuntimeError, match="HTTP status 502"):
        perform_request("topics")


def test_network_error(mock_api):
    mock_api.add("topics", urllib.error.URLError("no route to host"))

    with pytest.raises(RuntimeError, match="no route to host"):
        perform_request("topics")


def test_invalid_json(mock_api):
    mock_api.add("topics", b"<html>not json</html>")

    with pytest.raises(RuntimeError, match="Failed to parse JSON"):
        perform_request("topics")


def test_unexpected_response_format(mock_api):
    mock_api.add("topics", {"unexpected": True})

    with pytest.raises(RuntimeError, match="Unexpected response format"):
        perform_request("topics")


@pytest.mark.online
def test_perform_request_online():
    result = perform_request("languages", per_page=5)
    assert len(result) > 5
