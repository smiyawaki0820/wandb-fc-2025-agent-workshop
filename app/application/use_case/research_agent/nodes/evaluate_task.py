from langgraph.types import Command

from application.use_case.research_agent.models import ResearchAgentState
from core.logging import LogLevel
from domain.enums import BaseEnum
from domain.models import ManagedDocument 
from application.use_case.research_agent.models import TaskEvaluation
from infrastructure.blob_manager.base import BaseBlobManager
from infrastructure.llm_chain.enums import OpenAIModelName
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain


class NextNode(BaseEnum):
    # BUILD_RESEARCH_PLAN = "BuildResearchPlanNode"
    GENERATE_REPORT = "GenerateReportNode"


class EvaluateTaskNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/evaluate_task.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[NextNode]:
        return Command(goto=NextNode.GENERATE_REPORT.value, update=state)
        # task_evaluation: TaskEvaluation = self.run(
        #     reading_results=state.reading_results,
        #     goal_setting=state.goal,
        # )
        # is_completed = all(
        #     task.status == ManagedTaskStatus.COMPLETED
        #     for task in task_evaluation.criteria_evals
        # )
        # state.retry_count += not is_completed
        # return Command(
        #     goto=NextNode.GENERATE_REPORT if is_completed else NextNode.DECOMPOSE_QUERY,
        #     update=state,
        # )

    def run(
        self,
        managed_documents: list[ManagedDocument],
        goal_setting: str,
    ) -> TaskEvaluation:
        context = "\n".join(
            managed_document.to_string()
            for managed_document in managed_documents
        )
        chain = self._build_structured_chain(TaskEvaluation)
        inputs = {
            "context": context,
            "goal_setting": goal_setting,
        }
        return self.invoke(chain, inputs, verbose=True)
