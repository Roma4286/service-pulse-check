from abc import ABC, abstractmethod


class BaseChecker(ABC):
    @abstractmethod
    def check(self, url: str) -> tuple[bool, float]:
        pass