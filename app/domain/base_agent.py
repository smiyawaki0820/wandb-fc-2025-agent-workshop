from abc import ABC, abstractmethod
from functools import partial

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from core.logging import LogLevel, log


class LangGraphAgent(ABC):
    def __init__(
        self,
        log_level: LogLevel,
        checkpointer: MemorySaver | None,
        recursion_limit: int,
    ) -> None:
        self.log = partial(log, log_level=log_level, subject=self.__name__)
        self.checkpointer = checkpointer
        self.recursion_limit = recursion_limit
        self.graph = self._create_graph()

    @property
    def __name__(self) -> str:
        return str(self.__class__.__name__)

    @property
    def default_models(self) -> dict[str, str]:
        raise NotImplementedError

    def _llm(self, node_name: str, temperature: float = 0.0) -> ChatOpenAI:
        if node_name not in self.model_names:
            error_message = f"model_names does not have {node_name}"
            self.log(object="llm", message=error_message)
            raise KeyError(error_message)
        return ChatOpenAI(model=self.model_names[node_name], temperature=temperature)

    @abstractmethod
    def _create_graph(self) -> CompiledStateGraph:
        raise NotImplementedError

    def _interrupt_from_user(self, content: str, default_message: str | None = None) -> str:
        user_message = interrupt(content)
        if message := (user_message or default_message):
            return message
        error_message = "user_message is None and default_message is not set"
        self.log(object="interrupt_from_user", message=error_message)
        raise ValueError(error_message)
