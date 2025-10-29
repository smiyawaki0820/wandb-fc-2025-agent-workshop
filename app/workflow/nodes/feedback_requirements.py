from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command, interrupt

from app.workflow.models import ResearchAgentState
from app.core.logging import LogLevel
from app.infrastructure.llm_chain import BaseChain
from app.workflow.enums import Node


class FeedbackRequirementsNode(BaseChain):
    def __init__(
        self,
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        super().__init__(log_level)

    def __call__(self, state: ResearchAgentState) -> Command[Literal[Node.GATHER_REQUIREMENTS.value]]:
        self.log(object="feedback_requirements", message=f"state: {state}")
        feedback_items = interrupt(
            {
                "node": self.__name__,
                "inquiry_items": state.inquiry_items,
            },
        )
        for idx, previous_item in enumerate(state.inquiry_items):
            if current_item := feedback_items.get(previous_item.id):
                state.inquiry_items[idx] = current_item
                # messages に追加
                state.messages.extend(
                    [
                        AIMessage(content=current_item.question),
                        HumanMessage(content=current_item.answer),
                    ]
                )
        return Command(goto=Node.GATHER_REQUIREMENTS.value, update=state)
