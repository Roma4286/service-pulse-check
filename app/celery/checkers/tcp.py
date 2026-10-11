import logging
import socket
import time
from urllib.parse import urlsplit

from .base import BaseChecker

logger = logging.getLogger(__name__)


def parse_address(url: str) -> tuple[str, int]:
    if "://" in url:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    else:
        host, _, port_text = url.rpartition(":")
        port = int(port_text)

    return host, port


class TcpChecker(BaseChecker):
    def check(self, url: str, timeout_in_seconds: float) -> tuple[bool, float]:
        host, port = parse_address(url)

        start = time.monotonic()
        try:
            with socket.create_connection((host, port), timeout=timeout_in_seconds):
                is_up = True
        except OSError:
            is_up = False

        response_time = time.monotonic() - start
        return is_up, response_time
