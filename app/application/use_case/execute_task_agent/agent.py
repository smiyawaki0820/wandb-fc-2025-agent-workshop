from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import InMemorySaver, MemorySaver

from application.use_case.execute_task_agent.models import (
    ExecuteTaskAgentInputState,
    ExecuteTaskAgentState,
)
from core.logging import LogLevel
from domain.base_agent import LangGraphAgent
from domain.enums import BaseEnum
from infrastructure.blob_manager import BaseBlobManager, LocalBlobManager
from infrastructure.content_search_client import BaseContentSearchClient, ArxivSearchClient
from infrastructure.api_client.jina_client import JinaClient
from infrastructure.llm_chain.enums import OpenAIModelName
from application.use_case.execute_task_agent.nodes import (
    ReceiveTaskNode,
    SearchDocumentsNode,
    ReadDocumentsNode,
    ManageTaskNode,
)


class NodeNames(BaseEnum):
    RECEIVE_TASK = "ReceiveTaskNode"
    SEARCH_DOCUMENTS = "SearchDocumentsNode"
    READ_DOCUMENTS = "ReadDocumentsNode"
    MANAGE_TASK = "ManageTaskNode"


class ExecuteTaskAgent(LangGraphAgent):
    def __init__(
        self,
        blob_manager: BaseBlobManager,
        search_client: BaseContentSearchClient,
        jina_client: JinaClient,
        checkpointer: MemorySaver | None = None,
        log_level: LogLevel = LogLevel.DEBUG,
        recursion_limit: int = 1000,
    ) -> None:
        self.blob_manager = blob_manager
        self.search_client = search_client
        self.jina_client = jina_client
        self.receive_task_node = ReceiveTaskNode(
            model_name=OpenAIModelName.GPT_5_MINI,
            blob_manager=blob_manager,
            log_level=log_level,
            prompt_path="storage/prompts/execute_task_agent/nodes/receive_task.jinja",
        )
        self.search_documents_node = SearchDocumentsNode(
            search_client=search_client,
            log_level=log_level,
        )
        self.read_documents_node = ReadDocumentsNode(
            model_name=OpenAIModelName.GPT_5_MINI,
            blob_manager=blob_manager,
            jina_client=jina_client,
            log_level=log_level,
            prompt_path="storage/prompts/execute_task_agent/nodes/read_documents.jinja",
        )
        self.manage_task_node = ManageTaskNode(log_level)
        super().__init__(
            log_level=log_level,
            checkpointer=checkpointer,
            recursion_limit=recursion_limit,
        )

    def __call__(self) -> CompiledStateGraph:
        return self.graph

    def _create_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(
            state_schema=ExecuteTaskAgentState,
            input=ExecuteTaskAgentInputState,
            output=ExecuteTaskAgentState,
        )
        workflow.add_node(NodeNames.RECEIVE_TASK.value, self.receive_task_node)
        workflow.add_node(NodeNames.SEARCH_DOCUMENTS.value, self.search_documents_node)
        workflow.add_node(NodeNames.READ_DOCUMENTS.value, self.read_documents_node)
        workflow.add_node(NodeNames.MANAGE_TASK.value, self.manage_task_node)
        workflow.set_entry_point(NodeNames.RECEIVE_TASK.value)
        workflow.set_finish_point(NodeNames.MANAGE_TASK.value)
        return workflow.compile(checkpointer=self.checkpointer)


def create_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    blob_manager = LocalBlobManager()
    jina_client = JinaClient()
    search_client = ArxivSearchClient(blob_manager)
    agent = ExecuteTaskAgent(
        blob_manager=blob_manager,
        search_client=search_client,
        jina_client=jina_client,
        checkpointer=checkpointer,
        log_level=LogLevel.DEBUG,
        recursion_limit=1000,
    )
    return agent.graph



if __name__ == "__main__":
    import json
    from application.use_case.research_agent.models import ManagedTask

    graph = create_graph()
    research_plan = json.load(open("storage/fixtures/state_from_build-research-plan.json"))
    managed_task = ManagedTask.model_validate(research_plan["tasks"][0])
    initial_state = ExecuteTaskAgentInputState(goal=research_plan["goal"], task=managed_task)

    output = graph.invoke(
        initial_state,
        config={"recursion_limit": 1000},
    )

    with open("storage/fixtures/state_from_execute-task.json", "w") as fo:
        json.dump(output, fo, ensure_ascii=False, indent=4)
