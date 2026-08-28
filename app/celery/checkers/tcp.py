import socket
import time

from .base import BaseChecker


class TcpChecker(BaseChecker):
    def check(self, url: str, timeout_in_seconds: float) -> tuple[bool, float]:
        host, port = url.rsplit(":", 1)

        start = time.monotonic()
        try:
            with socket.create_connection((host, int(port)), timeout=timeout_in_seconds):
                status_code = True
        except OSError:
            status_code = False

        response_time = time.monotonic() - start
        return status_code, response_time
