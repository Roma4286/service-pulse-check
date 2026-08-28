from abc import ABC, abstractmethod


class BaseChecker(ABC):
    @abstractmethod
    def check(self, url: str, timeout_in_seconds: float) -> tuple[bool, float]:
        pass