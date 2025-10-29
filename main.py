import argparse

from langchain_core.messages import HumanMessage
from loguru import logger

from app.infrastructure.blob_manager.local import LocalBlobManager
from app.workflow.agent import create_graph
from app.workflow.models.state import ResearchAgentState, ResearchAgentOutputState
from app.workflow.agent import invoke_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the research agent")
    parser.add_argument(
        "-m",
        "--initial-message",
        type=str,
        default="AIエージェントの登場によりBPOが注目されるようになっていますが、今後注目される領域やビジネスモデルはどのようなものがあると考えられますか？",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    blob_manager = LocalBlobManager()
    graph = create_graph()

    input_data = ResearchAgentState(
        messages=[HumanMessage(content=args.initial_message)],
    )

    result: ResearchAgentOutputState = invoke_graph(
        graph=graph,
        input_data=input_data,
        config={"recursion_limit": 1000, "thread_id": "default"},
    )

    output_file = "storage/outputs/research_report.md"
    blob_manager.save_blob_as_str(result["research_report"], output_file)
    logger.success(f"Research report saved to {output_file}")


if __name__ == "__main__":
    main()
