from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from application.use_case.research_agent.models import ResearchAgentState
from core.logging import LogLevel
from domain.enums import BaseEnum
from infrastructure.llm_chain import BaseChain


class NextNode(BaseEnum):
    GATHER_REQUIREMENTS = "GatherRequirementsNode"


class FeedbackRequirementsNode(BaseChain):
    def __init__(
        self,
        default_feedback: str = "そのままの条件で検索し、調査してください。",
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        self.default_feedback = default_feedback
        super().__init__(log_level)

    def __call__(self, state: ResearchAgentState) -> Command[Literal["GatherRequirementsNode"]]:
        self.log(object="feedback_requirements", message=f"state: {state}")
        human_feedback = interrupt(
            {
                "node": self.__name__,
                "inquiry_items": state.inquiry_items,
            },
        ) or self.default_feedback
        state.messages.append(HumanMessage(content=human_feedback))
        return Command(goto=NextNode.GATHER_REQUIREMENTS.value, update=state)
