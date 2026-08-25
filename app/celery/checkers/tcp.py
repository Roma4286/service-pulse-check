import socket
import time

from .base import BaseChecker


class TcpChecker(BaseChecker):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def check(self, url: str) -> tuple[bool, float]:
        host, port = url.rsplit(":", 1)

        start = time.monotonic()
        try:
            with socket.create_connection((host, int(port)), timeout=self.timeout):
                status_code = True
        except OSError:
            status_code = False

        response_time = time.monotonic() - start
        return status_code, response_time
