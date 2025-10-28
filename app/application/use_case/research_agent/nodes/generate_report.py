from langgraph.graph import END
from langgraph.types import Command

from application.use_case.research_agent.models import (
    ResearchAgentState,
)
from application.use_case.research_agent.models.build_research_plan import (
    ReportSection,
    ManagedTask,
)
from core.logging import LogLevel
from domain.enums import BaseEnum
from infrastructure.blob_manager.base import BaseBlobManager
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from infrastructure.llm_chain.enums import OpenAIModelName


class NextNode(BaseEnum):
    END = END


class GenerateReportNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/generate_report.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ResearchAgentState) -> Command[NextNode]:
        report = self.run(
            goal=state.goal,
            storyline=state.storyline,
            executed_tasks=state.executed_tasks,
        )
        state.research_report = report
        return Command(goto=NextNode.END.value, update=state)

    def run(
        self,
        goal: str,
        storyline: list[ReportSection],
        executed_tasks: list[ManagedTask],
        verbose: bool = False,
    ) -> str:
        chain = self._build_chain()
        inputs = {
            "user_request": goal,
            "storyline": "\n".join(
                f"[{report_section.section}] {report_section.description}"
                for report_section in storyline
            ),
            "task_execution": "\n\n".join(
                (
                    f"### {managed_task.title}]\n"
                    f"#### タスク概要\n{managed_task.overview}\n"
                    f"#### 調査結果\n{managed_task.deliverable}"
                )
                for managed_task in executed_tasks
            ),
        }
        return self.invoke(chain, inputs, verbose)
