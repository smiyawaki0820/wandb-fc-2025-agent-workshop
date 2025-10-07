from enum import Enum
from typing import Iterator, Literal


class BaseEnum(Enum):
    @classmethod
    def to_list(cls) -> list[str]:
        return [item.value for item in cls]

    @classmethod
    def __iter__(cls) -> Iterator[str]:
        return iter(cls.to_list())

    @classmethod
    def to_options(cls) -> Literal[str, ...]:  # type: ignore
        options = tuple(cls.to_list())
        return Literal[*options]
