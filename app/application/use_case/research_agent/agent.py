from functools import partial

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from application.use_case.research_agent.models.state import (
    ResearchAgentState,
    ResearchAgentInputState,
    ResearchAgentOutputState,
)
from application.use_case.execute_task_agent.agent import ExecuteTaskAgent
from application.use_case.execute_task_agent.models import ExecuteTaskAgentInputState
from application.use_case.research_agent.nodes import (
    FeedbackRequirementsNode,
    GatherRequirementsNode,
    BuildResearchPlanNode,
    EvaluateTaskNode,
    GenerateReportNode,
)
from domain.enums import BaseEnum
from domain.models import ManagedDocument
from domain.base_agent import LangGraphAgent
from core.logging import log, LogLevel
from infrastructure.blob_manager import BaseBlobManager, LocalBlobManager
from infrastructure.llm_chain.enums import OpenAIModelName
from infrastructure.content_search_client import (
    BaseContentSearchClient, ArxivSearchClient, PerplexitySearchClient,
)
from infrastructure.api_client.jina_client import JinaClient


class NodeNames(BaseEnum):
    FEEDBACK_REQUIREMENTS = "FeedbackRequirementsNode"
    GATHER_REQUIREMENTS = "GatherRequirementsNode"
    BUILD_RESEARCH_PLAN = "BuildResearchPlanNode"
    EXECUTE_TASK_AGENT = "ExecuteTaskAgentNode"
    EVALUATE_TASK = "EvaluateTaskNode"
    GENERATE_REPORT = "GenerateReportNode"


class ResearchAgent(LangGraphAgent):
    def __init__(
        self,
        blob_manager: BaseBlobManager,
        search_client: BaseContentSearchClient,
        jina_client: JinaClient,
        checkpointer: MemorySaver | None = None,
        log_level: LogLevel = LogLevel.INFO,
        recursion_limit: int = 1000,
    ) -> None:
        self.log = partial(log, log_level=log_level, subject=self.__name__)
        self.checkpointer = checkpointer
        self.recursion_limit = recursion_limit
        self.blob_manager = blob_manager

        self.gather_requirements_node = GatherRequirementsNode(
            model_name=OpenAIModelName.GPT_5_NANO,
            blob_manager=blob_manager,
            log_level=log_level,
            prompt_path="storage/prompts/research_agent/nodes/gather_requirements.jinja",
        )
        self.feedback_requirements_node = FeedbackRequirementsNode(log_level=log_level)
        self.build_research_plan_node = BuildResearchPlanNode(
            model_name=OpenAIModelName.GPT_5_NANO,
            blob_manager=blob_manager,
            log_level=log_level,
            prompt_path="storage/prompts/research_agent/nodes/build_research_plan.jinja",
        )
        self.execute_task_agent = ExecuteTaskAgent(
            blob_manager=blob_manager,
            search_client=search_client,
            jina_client=jina_client,
            checkpointer=checkpointer,
            log_level=log_level,
            recursion_limit=recursion_limit,
        )
        self.evaluate_task_node = EvaluateTaskNode(
            model_name=OpenAIModelName.GPT_5_NANO,
            blob_manager=blob_manager,
            log_level=log_level,
            prompt_path="storage/prompts/research_agent/nodes/evaluate_task.jinja",
        )
        self.generate_report_node = GenerateReportNode(
            model_name=OpenAIModelName.GPT_5_NANO,
            blob_manager=blob_manager,
            log_level=log_level,
            prompt_path="storage/prompts/research_agent/nodes/generate_report.jinja",
        )
        self.graph = self._create_graph()
        # super().__init__(
        #     log_level=settings.LOG_LEVEL,
        #     checkpointer=checkpointer,
        #     recursion_limit=recursion_limit,
        # )
        pass

    @property
    def __name__(self) -> str:
        return str(self.__class__.__name__)

    def _create_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(
            state_schema=ResearchAgentState,
            input=ResearchAgentInputState,
            output=ResearchAgentOutputState,
        )
        workflow.add_node(NodeNames.GATHER_REQUIREMENTS.value, self.gather_requirements_node)
        workflow.add_node(NodeNames.FEEDBACK_REQUIREMENTS.value, self.feedback_requirements_node)
        workflow.add_node(NodeNames.BUILD_RESEARCH_PLAN.value, self.build_research_plan_node)
        workflow.add_node(NodeNames.EXECUTE_TASK_AGENT.value, self._execute_task)
        workflow.add_node(NodeNames.EVALUATE_TASK.value, self.evaluate_task_node)
        workflow.add_node(NodeNames.GENERATE_REPORT.value, self.generate_report_node)
        workflow.add_edge(NodeNames.EVALUATE_TASK.value, NodeNames.GENERATE_REPORT.value)
        workflow.set_entry_point(NodeNames.GATHER_REQUIREMENTS.value)
        workflow.set_finish_point(NodeNames.GENERATE_REPORT.value)
        return workflow.compile(checkpointer=self.checkpointer)

    def _execute_task(self, state: ExecuteTaskAgentInputState) -> dict[str, list[ManagedDocument]]:
        input_state = ExecuteTaskAgentInputState(goal=state.goal, task=state.task)
        output = self.execute_task_agent.graph.invoke(
            input_state,
            config={"recursion_limit": self.recursion_limit},
        )
        return {"managed_documents": output.get("managed_documents") or []}


def create_graph() -> CompiledStateGraph:
    blob_manager = LocalBlobManager()
    search_client = ArxivSearchClient(blob_manager)
    # search_client = PerplexitySearchClient(blob_manager)
    jina_client = JinaClient()
    agent = ResearchAgent(
        blob_manager=blob_manager,
        search_client=search_client,
        jina_client=jina_client,
        checkpointer=None,
        log_level=LogLevel.DEBUG,
        recursion_limit=1000,
    )
    return agent.graph


if __name__ == "__main__":
    from pprint import pformat
    from langchain_core.messages import HumanMessage
    from loguru import logger

    blob_manager = LocalBlobManager()
    graph = create_graph()
    messages = [
        HumanMessage(content="diffusion language modelについて調査"),
    ]

    for _, state in graph.stream(
        input=ResearchAgentState(messages=messages),
        config={"recursion_limit": 1000},
        stream_mode="updates",
        subgraphs=True,
    ):
        for node_name, value in state.items():
            logger.success(f"[{node_name}]")
            logger.info(f"{pformat(value)}")

    import pdb; pdb.set_trace()