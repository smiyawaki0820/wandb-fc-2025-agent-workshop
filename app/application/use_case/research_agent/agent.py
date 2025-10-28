from copy import deepcopy

from langgraph.checkpoint.memory import InMemorySaver, MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from loguru import logger

from application.use_case.research_agent.models.state import (
    ResearchAgentState,
    ResearchAgentInputState,
    ResearchAgentOutputState,
)
from application.use_case.research_agent.nodes import (
    FeedbackRequirementsNode,
    GatherRequirementsNode,
    BuildResearchPlanNode,
    ExecuteTaskNode,
    GenerateReportNode,
)
from domain.enums import BaseEnum, ManagedTaskStatus
from domain.base_agent import LangGraphAgent
from core.logging import LogLevel
from infrastructure.blob_manager import BaseBlobManager, LocalBlobManager
from infrastructure.llm_chain.enums import OpenAIModelName


class NodeNames(BaseEnum):
    FEEDBACK_REQUIREMENTS = "FeedbackRequirementsNode"
    GATHER_REQUIREMENTS = "GatherRequirementsNode"
    BUILD_RESEARCH_PLAN = "BuildResearchPlanNode"
    EXECUTE_TASK = "ExecuteTaskNode"
    GENERATE_REPORT = "GenerateReportNode"


class ResearchAgent(LangGraphAgent):
    def __init__(
        self,
        blob_manager: BaseBlobManager,
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
        self.execute_task_node = ExecuteTaskNode(
            model_name=OpenAIModelName.GPT_5_NANO,
            blob_manager=blob_manager,
            log_level=log_level,
            prompt_path="storage/prompts/research_agent/nodes/execute_task.jinja",
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
        workflow.add_node(
            NodeNames.GATHER_REQUIREMENTS.value, self.gather_requirements_node
        )
        workflow.add_node(
            NodeNames.FEEDBACK_REQUIREMENTS.value, self.feedback_requirements_node
        )
        workflow.add_node(
            NodeNames.BUILD_RESEARCH_PLAN.value, self.build_research_plan_node
        )
        workflow.add_node(NodeNames.EXECUTE_TASK.value, self.execute_task_node)
        workflow.add_node(NodeNames.GENERATE_REPORT.value, self.generate_report_node)
        workflow.set_entry_point(NodeNames.GATHER_REQUIREMENTS.value)
        workflow.set_finish_point(NodeNames.GENERATE_REPORT.value)
        return workflow.compile(checkpointer=self.checkpointer)


def create_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    blob_manager = LocalBlobManager()
    agent = ResearchAgent(
        blob_manager=blob_manager,
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
                    # 全ての質問に回答を求める場合
                    inquiry_items = deepcopy(interrupt_data.get("inquiry_items", []))
                    for idx, inquiry_item in enumerate(inquiry_items):
                        if inquiry_item.status in [ManagedTaskStatus.NOT_STARTED]:
                            question = inquiry_item.question
                            user_input = str(input(f"{question} > "))
                            inquiry_items[idx].answer = user_input or "NO ANSWER NEEDED"
                            inquiry_items[idx].status = ManagedTaskStatus.COMPLETED
                    return invoke_graph(
                        graph=graph,
                        input_data=Command(
                            resume={item.id: item for item in inquiry_items}
                        ),
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

    initial_message = "今後5年10年でAIの市場はどのように変化していくと考えられますか？またAIエージェントの登場によりBPOが注目されるようになっていますが、今後注目される領域やビジネスモデルはどのようなものがあると考えられますか？"
    # initial_message = str(input("調査したい内容を入力してください: "))
    messages = [
        HumanMessage(content=initial_message),
    ]

    result: ResearchAgentOutputState = invoke_graph(
        graph=graph,
        input_data=ResearchAgentState(messages=messages),
        config={"recursion_limit": 1000, "thread_id": "default"},
    )

    output_file = "storage/outputs/research_report.md"
    blob_manager.save_blob_as_str(result["research_report"], output_file)
    logger.success(f"Research report saved to {output_file}")
