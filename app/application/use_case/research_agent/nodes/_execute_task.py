from langchain_core.messages import BaseMessage, AIMessage
from langgraph.types import Command

from application.use_case.research_agent.models import (
    GatherRequirements, ManagedInquiryItem, ResearchAgentState,
)
from core.logging import LogLevel
from domain.enums import BaseEnum, ManagedTaskStatus
from infrastructure.blob_manager import BaseBlobManager
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from infrastructure.llm_chain.enums import OpenAIModelName


class NextNode(BaseEnum):
    FEEDBACK_REQUIREMENTS = "FeedbackRequirementsNode"
    BUILD_RESEARCH_PLAN = "BuildResearchPlanNode"


class ExecuteTaskNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/gather_requirements.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[NextNode.to_options()]:
        gather_requirements = self.run(state.messages, state.inquiry_items)
        state.inquiry_items = gather_requirements.update_inquiry_items(state.inquiry_items)
        state.inquiry_items += gather_requirements.inquiry_items
        if not gather_requirements.is_completed:
            state.messages.append(AIMessage(content=gather_requirements.response_to_user))
        return Command(
            goto=(
                NextNode.BUILD_RESEARCH_PLAN.value if gather_requirements.is_completed else
                NextNode.FEEDBACK_REQUIREMENTS.value
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
