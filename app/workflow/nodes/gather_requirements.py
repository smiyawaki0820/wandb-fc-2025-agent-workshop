from langchain_core.messages import BaseMessage, AIMessage
from langgraph.types import Command

from app.workflow.models import (
    GatherRequirements,
    ManagedInquiryItem,
    ResearchAgentState,
)
from app.core.logging import LogLevel
from app.domain.enums import BaseEnum, ManagedTaskStatus
from app.infrastructure.blob_manager import BaseBlobManager
from app.infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from app.infrastructure.llm_chain.enums import OpenAIModelName


class NextNode(BaseEnum):
    FEEDBACK_REQUIREMENTS = "FeedbackRequirementsNode"
    BUILD_RESEARCH_PLAN = "BuildResearchPlanNode"


class GatherRequirementsNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/gather_requirements.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[NextNode]:
        gather_requirements = self.run(state.messages, state.inquiry_items)
        # 既存の要件収集項目のステータスを更新
        state.inquiry_items = gather_requirements.update_inquiry_items(
            state.inquiry_items
        )
        # 新しい要件収集項目を追加
        state.inquiry_items += gather_requirements.inquiry_items
        return Command(
            goto=(
                NextNode.BUILD_RESEARCH_PLAN.value
                if gather_requirements.is_completed
                else NextNode.FEEDBACK_REQUIREMENTS.value
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


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, AIMessage
    from app.core.utils.nano_id import generate_id
    from app.infrastructure.blob_manager import LocalBlobManager

    blob_manager = LocalBlobManager()
    chain = GatherRequirementsNode(OpenAIModelName.GPT_5_MINI, blob_manager)

    sample_message = [
        HumanMessage(content="Transformersの論文を探しています。"),
        AIMessage(
            content="どのような分野や用途でTransformersの論文をお探しですか？（例：自然言語処理、画像認識、医療データ分析など）"
        ),
        HumanMessage(content="医療データの解析に活用したいと考えています。"),
    ]
    state_inquiry_items = [
        ManagedInquiryItem(
            id=generate_id(),
            status=ManagedTaskStatus.COMPLETED,
            question="検索対象とする期間（例：最近の年、過去10年、特定の期間など）を教えてください。",
            answer="最近の年",
        ),
        ManagedInquiryItem(
            id=generate_id(),
            status=ManagedTaskStatus.NOT_STARTED,
            question="どのような分野や用途でTransformersの論文をお探しですか？（例：自然言語処理、画像認識、医療データ分析など）",
            answer=None,
        ),
    ]
    gather_requirements = chain.run(sample_message, state_inquiry_items, verbose=True)

    state_inquiry_items = gather_requirements.update_inquiry_items(state_inquiry_items)
    state_inquiry_items += gather_requirements.inquiry_items

    for updated_item in state_inquiry_items:
        print(updated_item.model_dump_json(indent=2))
