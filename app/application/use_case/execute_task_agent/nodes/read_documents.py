from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.types import Command

from application.use_case.execute_task_agent.models import (
    ExecuteTaskAgentState,
)
from application.use_case.research_agent.models import ManagedTask
from application.use_case.execute_task_agent.models.read_documents import ReadDocumentResult
from core.logging import LogLevel
from domain.enums import BaseEnum, ManagedTaskStatus
from domain.models import ManagedDocument
from infrastructure.blob_manager import BaseBlobManager
from infrastructure.llm_chain.openai_chain import BaseOpenAIChain
from infrastructure.llm_chain.enums import OpenAIModelName
from infrastructure.api_client.jina_client import JinaClient


class NextNode(BaseEnum):
    MANAGE_TASK = "ManageTaskNode"


class ReadDocumentsNode(BaseOpenAIChain):
    def __init__(
        self,
        model_name: OpenAIModelName,
        blob_manager: BaseBlobManager,
        jina_client: JinaClient,
        log_level: LogLevel = LogLevel.DEBUG,
        prompt_path: str = "storage/prompts/execute_task_agent/nodes/read_documents.jinja",
    ) -> None:
        self.jina_client = jina_client
        super().__init__(model_name, blob_manager, log_level, prompt_path)

    def __call__(self, state: ExecuteTaskAgentState) -> Command[NextNode]:
        read_document_results = self.batch_run(
            state.goal,
            state.task,
            state.managed_documents,
        )
        for idx, read_document_result in enumerate(read_document_results):
            if read_document_result is None:
                continue
            state.managed_documents[idx].summary = read_document_result.summary
            if read_document_result.is_related:
                state.managed_documents[idx].status = ManagedTaskStatus.COMPLETED
            else:
                state.managed_documents[idx].status = ManagedTaskStatus.PENDING
        return Command(goto=NextNode.MANAGE_TASK.value, update=state)

    def run(
        self,
        goal: str,
        task: ManagedTask,
        managed_document: ManagedDocument,
        idx: int = 0,
        verbose: bool = False,
    ) -> tuple[ReadDocumentResult | None, int]:
        markdown = self.jina_client.pdf_to_markdown(managed_document.url)
        if markdown is None:
            return (None, idx)
        chain = self._build_structured_chain(ReadDocumentResult)
        inputs = {
            "goal": goal,
            "task": task,
            "output_format": ReadDocumentResult.model_json_schema(),
            "document_markdown": markdown,
        }
        return self.invoke(chain, inputs, verbose=verbose), idx

    def batch_run(
        self,
        goal: str,
        task: ManagedTask,
        managed_documents: list[ManagedDocument],
        verbose: bool = False,
    ) -> list[ReadDocumentResult]:
        read_document_results: list[ReadDocumentResult] = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.run, goal, task, managed_document, idx, verbose)
                for idx, managed_document in enumerate(managed_documents)
            ]
            for future in as_completed(futures):
                read_document_result, idx = future.result()
                if read_document_result is None:
                    continue
                read_document_results.append((idx, read_document_result))
        return [
            read_document_result
            for idx, read_document_result in sorted(read_document_results, key=lambda x: x[0])
        ]
