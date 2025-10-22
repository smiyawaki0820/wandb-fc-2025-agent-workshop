from langgraph.types import Command

from application.use_case.execute_task_agent.models import ExecuteTaskAgentState
from application.use_case.research_agent.models import ManagedTask
from core.logging import LogLevel
from domain.enums import BaseEnum, ManagedTaskStatus
from domain.models import Document, ManagedDocument
from infrastructure.llm_chain.base import BaseChain
from infrastructure.content_search_client import BaseContentSearchClient


class NextNode(BaseEnum):
    READ_DOCUMENTS = "ReadDocumentsNode"


class SearchDocumentsNode(BaseChain):
    def __init__(
        self,
        search_client: BaseContentSearchClient,
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        self.search_client = search_client
        super().__init__(log_level)

    def __call__(self, state: ExecuteTaskAgentState) -> Command[NextNode.to_options()]:
        documents = self.run(state.task)
        managed_documents: list[ManagedDocument] = []
        for document in documents:
            managed_document = ManagedDocument(
                task_id=state.task.id,
                status=ManagedTaskStatus.NOT_STARTED,
                id=document.id,
                title=document.title,
                url=document.url,
                abstract=document.abstract,
                authors=document.authors,
            )
            managed_documents.append(managed_document)
        state.managed_documents = managed_documents
        return Command(goto=NextNode.READ_DOCUMENTS.value, update=state)

    def run(self, task: ManagedTask) -> list[Document]:
        return self.search_client.search(task.summary)



if __name__ == "__main__":
    import json
    from infrastructure.blob_manager import LocalBlobManager
    from infrastructure.content_search_client import ArxivSearchClient

    blob_manager = LocalBlobManager()
    search_client = ArxivSearchClient(blob_manager)
    chain = SearchDocumentsNode(search_client)

    research_plan = json.load(open("storage/fixtures/build_research_plan.json"))
    managed_task = ManagedTask.model_validate(research_plan["managed_tasks"][1])

    documents = chain.run(managed_task)
    for document in documents:
        print(document.model_dump_json(indent=2))
        print("-" * 100)

    import ipdb; ipdb.set_trace()