from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.types import Command, Send

from application.use_case.execute_task_agent.models import (
    ExecuteTaskAgentState,
    ReceiveTaskExecution,
    ManagedTaskExecution,
)
from application.use_case.research_agent.models import ManagedTask
from core.logging import LogLevel
from domain.enums import BaseEnum, ManagedTaskStatus
from infrastructure.blob_manager import BaseBlobManager
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from infrastructure.llm_chain.enums import OpenAIModelName


class NextNode(BaseEnum):
    SEARCH_DOCUMENTS = "SearchDocumentsNode"
    MANAGE_TASK = "ManageTaskNode"


class ReceiveTaskNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/execute_task_agent/nodes/receive_task.jinja",
    ) -> None:
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ExecuteTaskAgentState) -> Command[NextNode]:
        managed_task_execution = self._run_single_task(state.task)
        match managed_task_execution.status:
            case ManagedTaskStatus.IN_PROGRESS:
                next_node = NextNode.SEARCH_DOCUMENTS.value
            case ManagedTaskStatus.COMPLETED:
                next_node = NextNode.MANAGE_TASK.value
            case ManagedTaskStatus.FAILED:
                next_node = NextNode.MANAGE_TASK.value
            case _:
                error_message = f"Invalid managed task status: {managed_task_execution.status}"
                self.logger.error(error_message)
                raise ValueError(error_message)
        return Command(goto=next_node, update=state)

    def _call__(self, state: ExecuteTaskAgentState) -> Command[NextNode]:
        managed_task_executions = self.run(state.task)
        state.task_executions = managed_task_executions
        gotos = []
        for managed_task_execution in managed_task_executions:
            match managed_task_execution.status:
                case ManagedTaskStatus.IN_PROGRESS:
                    next_node = NextNode.SEARCH_DOCUMENTS.value
                case ManagedTaskStatus.COMPLETED:
                    next_node = NextNode.MANAGE_TASK.value
                case ManagedTaskStatus.FAILED:
                    next_node = NextNode.MANAGE_TASK.value
                case _:
                    error_message = f"Invalid managed task status: {managed_task_execution.status}"
                    self.logger.error(error_message)
                    raise ValueError(error_message)
            gotos.append(Send(next_node))
        return Command(goto=gotos, update=state)

    def _run_single_task(
        self,
        task: ManagedTask,
        verbose: bool = False,
    ) -> ReceiveTaskExecution:
        chain = self._build_structured_chain(ReceiveTaskExecution)
        inputs = {
            "task": task,
            "output_format": ReceiveTaskExecution.model_json_schema(),
        }
        task_execution = self.invoke(chain, inputs, verbose=verbose)
        if task_execution.need_research:
            status = ManagedTaskStatus.IN_PROGRESS
        elif task_execution.task_response:
            status = ManagedTaskStatus.COMPLETED
        else:
            status = ManagedTaskStatus.FAILED
        return ManagedTaskExecution(
            id=task.id,
            status=status,
            need_research=task_execution.need_research,
            task_response=task_execution.task_response,
        )

    def run(
        self,
        tasks: list[ManagedTask],
        verbose: bool = False,
    ) -> list[ManagedTaskExecution]:
        task_executions: list[ManagedTaskExecution] = []
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = [
                executor.submit(self._run_single_task, task, verbose)
                for task in tasks
            ]
            for future in as_completed(futures):
                task_execution = future.result()
                task_executions.append(task_execution)
        return task_executions



if __name__ == "__main__":
    import json
    from infrastructure.blob_manager import LocalBlobManager

    blob_manager = LocalBlobManager()
    chain = ReceiveTaskNode(OpenAIModelName.GPT_5_NANO, blob_manager)

    research_plan = json.load(open("storage/fixtures/build_research_plan.json"))
    managed_tasks = [
        ManagedTask.model_validate(managed_task)
        for managed_task in research_plan["managed_tasks"]
    ]
    managed_task_executions = chain.run(managed_tasks, verbose=True)

    for managed_task_execution in managed_task_executions:
        print(managed_task_execution.model_dump_json(indent=2))
        print("-" * 100)
