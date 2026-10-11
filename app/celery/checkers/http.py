import time

import requests

from .base import BaseChecker


class HttpChecker(BaseChecker):
    def check(self, url: str, timeout_in_seconds: float) -> tuple[bool, float]:
        start = time.monotonic()
        try:
            response = requests.get(url, timeout=timeout_in_seconds, stream=True)
            response.close()
            is_up = 200 <= response.status_code < 400
        except requests.RequestException:
            is_up = False

        response_time = time.monotonic() - start
        return is_up, response_time
