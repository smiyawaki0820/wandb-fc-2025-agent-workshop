from typing import Literal

from langchain_core.messages import BaseMessage
from langgraph.types import Command, Send

from app.core.logging import LogLevel
from app.domain.enums import Priority
from app.infrastructure.blob_manager import BaseBlobManager
from app.infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from app.infrastructure.llm_chain.enums import OpenAIModelName
from app.workflow.enums import Node
from app.workflow.models import (
    ResearchAgentState,
    ResearchPlan,
    ManagedInquiryItem,
    ExecuteTaskState,
)


class BuildResearchPlanNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        target_priority: Priority = Priority.HIGH,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/build_research_plan.jinja",
    ) -> None:
        self.target_priority = target_priority
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[Literal[Node.EXECUTE_TASK.value]]:
        research_plan = self.run(
            messages=state.messages,
            inquiry_items=state.inquiry_items,
        )
        state.goal = research_plan.goal
        state.tasks = research_plan.managed_tasks
        state.storyline = research_plan.storyline
        gotos = []
        for managed_task in state.tasks:
            goto = Send(
                Node.EXECUTE_TASK.value,
                ExecuteTaskState(goal=state.goal, task=managed_task),
            )
            gotos.append(goto)
        return Command(goto=gotos, update=state)

    def run(
        self,
        messages: list[BaseMessage],
        inquiry_items: list[ManagedInquiryItem],
        verbose: bool = False,
    ) -> ResearchPlan:
        chain = self._build_structured_chain(ResearchPlan)
        inputs = {
            "output_format": ResearchPlan.model_json_schema(),
            "inquiry_items": inquiry_items,
            "conversation_history": messages,
        }
        research_plan = self.invoke(chain, inputs, verbose)
        research_plan.tasks = [
            task
            for task in research_plan.tasks
            if task.priority in Priority.up_to(self.target_priority)
        ]
        return research_plan
