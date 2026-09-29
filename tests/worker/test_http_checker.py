from unittest.mock import Mock

import pytest
import requests

from app.celery.checkers.http import HttpChecker


def test_check_requests_url_with_timeout(fake_get):
    HttpChecker().check("https://example.com", 2.5)

    fake_get.assert_called_once_with("https://example.com", timeout=2.5)


@pytest.mark.parametrize("status_code", [200, 204, 301, 399])
def test_check_treats_2xx_and_3xx_as_up(fake_get, status_code):
    fake_get.return_value = Mock(status_code=status_code)

    is_up, _ = HttpChecker().check("https://example.com", 2.5)

    assert is_up is True


@pytest.mark.parametrize("status_code", [400, 404, 500, 503])
def test_check_treats_4xx_and_5xx_as_down(fake_get, status_code):
    fake_get.return_value = Mock(status_code=status_code)

    is_up, _ = HttpChecker().check("https://example.com", 2.5)

    assert is_up is False


@pytest.mark.parametrize(
    "error",
    [requests.Timeout(), requests.ConnectionError(), requests.TooManyRedirects()],
    ids=["timeout", "connection-error", "too-many-redirects"],
)
def test_check_treats_request_errors_as_down(fake_get, error):
    fake_get.side_effect = error

    is_up, _ = HttpChecker().check("https://example.com", 2.5)

    assert is_up is False


@pytest.mark.usefixtures("fake_get", "fake_clock")
def test_check_measures_response_time():
    _, response_time = HttpChecker().check("https://example.com", 2.5)

    assert response_time == 0.25


@pytest.mark.usefixtures("fake_clock")
def test_check_measures_response_time_when_request_fails(fake_get):
    fake_get.side_effect = requests.Timeout()

    _, response_time = HttpChecker().check("https://example.com", 2.5)

    assert response_time == 0.25
