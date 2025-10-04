from langchain_core.messages import BaseMessage
from langgraph.types import Command

from application.use_case.research_agent.models import GatherRequirements, ManagedInquiryItem, ResearchAgentState
from core.config import settings
from core.utils.datetime_utils import get_current_time
from domain.enums import BaseEnum, ManagedTaskStatus
from infrastructure.blob_manager.base import BaseBlobManager
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from infrastructure.llm_chain.enums import OpenAIModelName


class NextNode(BaseEnum):
    HUMAN_FEEDBACK = "human_feedback"
    GOAL_SETTING = "goal_setting"


class GatherRequirementsChain(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: str = settings.LOG_LEVEL,
        prompt_path: str = "storage/prompts/chains/gather_requirements.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[NextNode]:
        gather_requirements = self.run(state.messages)
        state.inquiry_items = gather_requirements.update_inquiry_items(state.inquiry_items)
        state.inquiry_items += gather_requirements.inquiry_items
        is_completed = all(
            item.status == ManagedTaskStatus.COMPLETED
            for item in state.inquiry_items
        )
        return Command(
            goto=NextNode.GOAL_SETTING if is_completed else NextNode.HUMAN_FEEDBACK,
            update=state,
        )

    def run(self, messages: list[BaseMessage], managed_inquiry_items: list[ManagedInquiryItem]) -> GatherRequirements:
        chain = self._build_structured_chain(GatherRequirements)
        return self.invoke(
            chain,
            {
                "current_date": get_current_time(),
                "conversation_history": messages,
                "managed_inquiry_items": managed_inquiry_items,
            }
        )



if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, AIMessage
    from loguru import logger
    from ulid import ULID

    from infrastructure.blob_manager.local import LocalBlobManager

    blob_manager = LocalBlobManager()
    chain = GatherRequirementsChain(OpenAIModelName.GPT_4O_MINI, blob_manager)

    sample_message = [
        HumanMessage(content="データ分析業務における要件定義書を作成する"),
        AIMessage(content="具体的な学術分野や主題領域は何ですか？"),
        HumanMessage(content="医療系のデータ分析業務を行う"),
    ]
    state_inquiry_items = [
        ManagedInquiryItem(
            id=str(ULID()),
            status=ManagedTaskStatus.NOT_STARTED,
            question="具体的な学術分野や主題領域は何ですか？",
            answer=None,
        ),
    ]

    gather_requirements = chain.run(sample_message, state_inquiry_items)
    logger.debug(gather_requirements.model_dump_json(indent=2))

    state_inquiry_items = gather_requirements.update_inquiry_items(state_inquiry_items)
    state_inquiry_items += gather_requirements.inquiry_items

    for updated_item in state_inquiry_items:
        print(updated_item.model_dump_json(indent=2))
