import traceback

from langchain.agents import create_agent
from langgraph.types import Command
from langchain_core.tools.structured import StructuredTool

from application.use_case.research_agent.models import (
    ExecuteTaskState,
)
from application.use_case.research_agent.models.build_research_plan import TaskType
from application.use_case.research_agent.tools import search_web, submit_content
from domain.enums import TaskStatus
from core.logging import LogLevel, log
from core.middleware import handle_tool_errors, validate_output
from domain.enums import BaseEnum
from application.use_case.research_agent.models.build_research_plan import ManagedTask
from infrastructure.llm_chain import BaseChain
from infrastructure.llm_chain.enums import OpenAIModelName
from infrastructure.blob_manager.base import BaseBlobManager


class NextNode(BaseEnum):
    EXECUTE_TASK = "ExecuteTaskNode"
    GENERATE_REPORT = "GenerateReportNode"


class ExecuteTaskNode(BaseChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/research_agent/nodes/execute_task.jinja",
    ) -> None:
        self.model_name = f"openai:{model_name.value}"
        self.blob_manager = blob_manager
        self.prompt_path = prompt_path
        super().__init__(log_level)

    @property
    def tools(self) -> dict[TaskType, StructuredTool]:
        return {
            TaskType.SEARCH: search_web,
        }

    def __call__(self, state: ExecuteTaskState) -> Command[NextNode]:
        managed_task_execution = self.run(state)
        return Command(
            goto=NextNode.GENERATE_REPORT.value,
            update={
                "executed_tasks": [managed_task_execution],
            },
        )

    def run(self, state: ExecuteTaskState) -> ManagedTask:
        managed_task = state.task
        selected_tools = [submit_content]
        for key in managed_task.required_capabilities:
            if tool := self.tools.get(key):
                selected_tools.append(tool)  # noqa: PERF401
        prompt_template = self.blob_manager.read_blob_as_template(self.prompt_path)
        prompt = prompt_template.render(
            goal=state.goal,
            title=managed_task.title,
            overview=managed_task.overview,
            objective=managed_task.objective,
            research_scope=managed_task.research_scope,
        )
        agent = create_agent(
            model=self.model_name,
            tools=selected_tools,
            system_prompt=prompt,
            middleware=[
                handle_tool_errors,
                validate_output,
            ],
        ).with_config({"recursion_limit": 50})
        try:
            response_content = agent.invoke({})
            from loguru import logger
            logger.error(type(response_content))
            return ManagedTask(
                id=managed_task.id,
                status=TaskStatus.COMPLETED.value,  # Use the value (str), not enum object
                deliverable=str(response_content),
                title=managed_task.title,
                overview=managed_task.overview,
                objective=managed_task.objective,
                research_scope=managed_task.research_scope,
                priority=managed_task.priority,
                required_capabilities=managed_task.required_capabilities,
            )
        except Exception as e:
            error_message = f"Error executing task: {e!s}\n{traceback.format_exc()}"
            log(LogLevel.ERROR, subject="ExecuteTaskNode", object="run", message=error_message)
            return ManagedTask(
                id=managed_task.id,
                status=TaskStatus.FAILED.value,
                deliverable=None,
                title=managed_task.title,
                overview=managed_task.overview,
                objective=managed_task.objective,
                research_scope=managed_task.research_scope,
                priority=managed_task.priority,
                required_capabilities=managed_task.required_capabilities,
            )
