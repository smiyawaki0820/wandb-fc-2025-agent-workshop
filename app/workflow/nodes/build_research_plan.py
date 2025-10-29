from langchain_core.messages import BaseMessage
from langgraph.types import Command, Send

from app.workflow.models import (
    ResearchAgentState,
    ResearchPlan,
    ManagedInquiryItem,
    ExecuteTaskState,
)
from app.core.logging import LogLevel
from app.domain.enums import BaseEnum, Priority
from app.infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from app.infrastructure.llm_chain.enums import OpenAIModelName
from app.infrastructure.blob_manager.base import BaseBlobManager


class NextNode(BaseEnum):
    EXECUTE_TASK = "ExecuteTaskNode"


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

    def __call__(self, state: ResearchAgentState) -> Command[NextNode]:
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
                NextNode.EXECUTE_TASK.value,
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


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage
    from app.infrastructure.blob_manager.local import LocalBlobManager
    from app.domain.enums import Priority, ManagedTaskStatus
    from app.domain.models import ManagedInquiryItem
    from app.core.utils.nano_id import generate_id

    blob_manager = LocalBlobManager()
    decomposer = BuildResearchPlanNode(OpenAIModelName.GPT_5_NANO, blob_manager)
    messages = [
        HumanMessage(content="シーンテキストを考慮したテキスト画像検索について調査"),
    ]
    inquiry_items = [
        ManagedInquiryItem(
            id=generate_id(),
            question="なぜシーンテキストを考慮したテキスト画像検索が必要なのか？",
            answer=None,
            priority=Priority.HIGH,
            status=ManagedTaskStatus.PENDING,
        ),
    ]
    research_plan = decomposer.run(
        messages=messages, inquiry_items=inquiry_items, verbose=True
    )
    print(research_plan.model_dump_json(indent=2))
