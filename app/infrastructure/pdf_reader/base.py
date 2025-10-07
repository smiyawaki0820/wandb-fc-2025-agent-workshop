from abc import ABC
from functools import partial

from core.logging import LogLevel, log


class BasePdfReader(ABC):
    def __init__(self, log_level: LogLevel) -> None:
        self.log = partial(
            log,
            log_level=log_level,
            subject=self.__name__,
        )

    @property
    def __name__(self) -> str:
        return str(self.__class__.__name__)
