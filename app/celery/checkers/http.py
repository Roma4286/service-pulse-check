import time

import requests

from .base import BaseChecker

class HttpChecker(BaseChecker):
    def check(self, url: str, timeout_in_seconds: float) -> tuple[bool, float]:
        start = time.monotonic()
        try:
            response = requests.get(url, timeout=timeout_in_seconds)
            status_code = 200 <= response.status_code < 400
        except requests.RequestException:
            status_code = False

        response_time = time.monotonic() - start
        return status_code, response_time
