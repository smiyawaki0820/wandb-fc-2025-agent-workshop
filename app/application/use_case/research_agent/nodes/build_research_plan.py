from langchain_core.messages import BaseMessage
from langgraph.types import Command, Send

from application.use_case.execute_task_agent.models import ExecuteTaskAgentInputState
from application.use_case.research_agent.models import (
    ResearchAgentState, ResearchPlan, ManagedInquiryItem,
)
from core.logging import LogLevel
from domain.enums import BaseEnum, Priority
from domain.models import ManagedDocument
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from infrastructure.llm_chain.enums import OpenAIModelName
from infrastructure.blob_manager.base import BaseBlobManager


class NextNode(BaseEnum):
    EXECUTE_TASK_AGENT = "ExecuteTaskAgentNode"


class BuildResearchPlanNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/build_research_plan.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[NextNode]:
        research_plan = self.run(
            messages=state.messages,
            inquiry_items=state.inquiry_items,
            managed_documents=state.managed_documents,
            improvement_hint=state.goal,
        )
        state.tasks = research_plan.managed_tasks
        # タスクごとに ExecuteTaskAgent に渡す
        gotos = []
        for managed_task in state.tasks:
            goto = Send(
                NextNode.EXECUTE_TASK_AGENT.value,
                ExecuteTaskAgentInputState(goal=state.goal, task=managed_task),
            )
            gotos.append(goto)
        return Command(goto=gotos, update=state)

    def run(
        self,
        messages: list[BaseMessage],
        inquiry_items: list[ManagedInquiryItem],
        managed_documents: list[ManagedDocument] | None = None,
        improvement_hint: str | None = None,
        verbose: bool = False,
    ) -> ResearchPlan:
        chain = self._build_structured_chain(ResearchPlan)
        inputs = {
            "research_medium": "arXiv",
            "output_format": ResearchPlan.model_json_schema(),
            "inquiry_items": inquiry_items,
            "conversation_history": messages,
            "managed_documents": managed_documents or [],
            "improvement_hint": improvement_hint,
        }
        research_plan = self.invoke(chain, inputs, verbose)
        # TODO: 今回は優先度が高いタスクのみを採用する
        research_plan.tasks = [
            task for task in research_plan.tasks
            if task.priority == Priority.HIGH
        ]
        return research_plan



if __name__ == "__main__":
    from langchain_core.messages import HumanMessage
    from infrastructure.blob_manager.local import LocalBlobManager
    from domain.enums import Priority, ManagedTaskStatus
    from domain.models import ManagedInquiryItem
    from core.utils.nano_id import generate_id

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
    research_plan = decomposer.run(messages=messages, inquiry_items=inquiry_items, verbose=True)
    print(research_plan.model_dump_json(indent=2))
