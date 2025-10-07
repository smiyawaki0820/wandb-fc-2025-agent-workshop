from abc import ABC, abstractmethod
from functools import partial

from core.logging import LogLevel, log
from domain.models import Document


class BaseContentSearchClient(ABC):
    def __init__(self, log_level: LogLevel) -> None:
        self.log = partial(
            log,
            log_level=log_level,
            subject=self.__name__,
        )

    @property
    def __name__(self) -> str:
        return str(self.__class__.__name__)

    @abstractmethod
    def search(self, user_request: str) -> list[Document]:
        pass
