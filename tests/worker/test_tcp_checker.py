import socket

import pytest

from app.celery.checkers.tcp import TcpChecker


def test_check_connects_to_host_and_port_with_timeout(fake_create_connection):
    TcpChecker().check("db.example.com:5432", 2.5)

    fake_create_connection.assert_called_once_with(
        ("db.example.com", 5432), timeout=2.5
    )


def test_check_splits_port_off_ipv6_address(fake_create_connection):
    TcpChecker().check("::1:8080", 2.5)

    fake_create_connection.assert_called_once_with(("::1", 8080), timeout=2.5)


@pytest.mark.parametrize(
    ("url", "address"),
    [
        ("http://db.example.com:5432/", ("db.example.com", 5432)),
        ("tcp://db.example.com:5432", ("db.example.com", 5432)),
        ("http://[::1]:8080/", ("::1", 8080)),
    ],
    ids=["http-url-as-stored-by-api", "tcp-scheme", "bracketed-ipv6"],
)
def test_check_gets_host_and_port_from_url(fake_create_connection, url, address):
    TcpChecker().check(url, 2.5)

    fake_create_connection.assert_called_once_with(address, timeout=2.5)


@pytest.mark.parametrize(
    "url",
    ["db.example.com", "db.example.com:port", "http://db.example.com:99999/"],
    ids=["no-port", "non-numeric-port", "port-out-of-range"],
)
def test_check_raises_on_invalid_port(fake_create_connection, url):
    with pytest.raises(ValueError):
        TcpChecker().check(url, 2.5)

    fake_create_connection.assert_not_called()


def test_check_closes_connection(fake_create_connection):
    TcpChecker().check("db.example.com:5432", 2.5)

    fake_create_connection.return_value.__exit__.assert_called_once()


@pytest.mark.usefixtures("fake_create_connection")
def test_check_treats_successful_connection_as_up():
    is_up, _ = TcpChecker().check("db.example.com:5432", 2.5)

    assert is_up is True


@pytest.mark.parametrize(
    "error",
    [ConnectionRefusedError(), TimeoutError(), socket.gaierror()],
    ids=["refused", "timeout", "dns-failure"],
)
def test_check_treats_connection_errors_as_down(fake_create_connection, error):
    fake_create_connection.side_effect = error

    is_up, _ = TcpChecker().check("db.example.com:5432", 2.5)

    assert is_up is False


@pytest.mark.usefixtures("fake_create_connection", "fake_clock")
def test_check_measures_response_time():
    _, response_time = TcpChecker().check("db.example.com:5432", 2.5)

    assert response_time == 0.25


def test_check_connects_to_real_listening_socket():
    with socket.create_server(("127.0.0.1", 0)) as server:
        port = server.getsockname()[1]

        is_up, _ = TcpChecker().check(f"127.0.0.1:{port}", 2.5)

    assert is_up is True
