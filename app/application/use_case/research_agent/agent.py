from functools import partial

from langgraph.checkpoint.memory import InMemorySaver, MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

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
from domain.enums import BaseEnum, ManagedTaskStatus
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
        super().__init__(
            log_level=log_level,
            checkpointer=checkpointer,
            recursion_limit=recursion_limit,
        )

    def _create_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(
            state_schema=ResearchAgentState,
            input_schema=ResearchAgentInputState,
            output_schema=ResearchAgentOutputState,
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
            config={"recursion_limit": self.recursion_limit, "thread_id": "subtask"},
        )
        return {"managed_documents": output.get("managed_documents") or []}


def create_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    blob_manager = LocalBlobManager()
    search_client = ArxivSearchClient(blob_manager)
    # search_client = PerplexitySearchClient(blob_manager)
    jina_client = JinaClient()
    agent = ResearchAgent(
        blob_manager=blob_manager,
        search_client=search_client,
        jina_client=jina_client,
        checkpointer=checkpointer,
        log_level=LogLevel.DEBUG,
        recursion_limit=1000,
    )
    return agent.graph


def invoke_graph(
    graph: CompiledStateGraph,
    input_data: dict | Command,
    config: dict,
) -> dict:
    result = graph.invoke(
        input=input_data,
        config=config,
    )
    for interrupt in result.get("__interrupt__", []):
        if interrupt_data := getattr(interrupt, "value", None):
            match interrupt_data.get("node"):
                case NodeNames.FEEDBACK_REQUIREMENTS.value:
                    answers = []
                    # 全ての質問に回答を求める場合
                    for inquiry_item in interrupt_data.get("inquiry_items", []):
                        if inquiry_item.status in [ManagedTaskStatus.NOT_STARTED]:
                            question = inquiry_item.question
                            user_input = str(input(f"{question} > "))
                            answers.append(f"{question}: {user_input or 'NO ANSWER NEEDED'}")
                    return invoke_graph(
                        graph=graph,
                        input_data=Command(resume="\n".join(answers)),
                        config=config,
                    )
                case _:
                    error_message = f"Unknown node: {interrupt_data.get('node')}"
                    raise ValueError(error_message)
    return result


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    blob_manager = LocalBlobManager()
    graph = create_graph()

    initial_message = str(input("調査したい内容を入力してください: "))
    messages = [
        HumanMessage(content=initial_message),
    ]

    result = invoke_graph(
        graph=graph,
        input_data=ResearchAgentState(messages=messages),
        config={"recursion_limit": 1000, "thread_id": "default"},
    )
    print(result)
