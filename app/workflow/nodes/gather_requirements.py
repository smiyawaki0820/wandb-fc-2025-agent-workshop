from typing import Literal

from langchain_core.messages import BaseMessage
from langgraph.types import Command

from app.workflow.models import (
    GatherRequirements,
    ManagedInquiryItem,
    ResearchAgentState,
)
from app.core.logging import LogLevel
from app.infrastructure.blob_manager import BaseBlobManager
from app.infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from app.infrastructure.llm_chain.enums import OpenAIModelName
from app.workflow.enums import Node


class GatherRequirementsNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/gather_requirements.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(
        self,
        state: ResearchAgentState
    ) -> Command[Literal[Node.FEEDBACK_REQUIREMENTS.value, Node.BUILD_RESEARCH_PLAN.value]]:
        gather_requirements = self.run(state.messages, state.inquiry_items)
        # 既存の要件収集項目のステータスを更新
        state.inquiry_items = gather_requirements.update_inquiry_items(
            state.inquiry_items
        )
        # 新しい要件収集項目を追加
        state.inquiry_items += gather_requirements.inquiry_items
        return Command(
            goto=(
                Node.BUILD_RESEARCH_PLAN.value
                if gather_requirements.is_completed
                else Node.FEEDBACK_REQUIREMENTS.value
            ),
            update=state,
        )

    def run(
        self,
        messages: list[BaseMessage],
        managed_inquiry_items: list[ManagedInquiryItem],
        verbose: bool = False,
    ) -> GatherRequirements:
        chain = self._build_structured_chain(GatherRequirements)
        inputs = {
            "conversation_history": messages,
            "managed_inquiry_items": managed_inquiry_items,
            "output_format": GatherRequirements.model_json_schema(),
        }
        return self.invoke(chain, inputs, verbose)
