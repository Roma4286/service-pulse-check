import time

import requests

from .base import BaseChecker

class HttpChecker(BaseChecker):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def check(self, url: str) -> tuple[bool, float]:
        start = time.monotonic()
        try:
            response = requests.get(url, timeout=self.timeout)
            status_code = True if response.status_code == 200 else False
        except requests.RequestException:
            status_code = False

        response_time = time.monotonic() - start
        return status_code, response_time
