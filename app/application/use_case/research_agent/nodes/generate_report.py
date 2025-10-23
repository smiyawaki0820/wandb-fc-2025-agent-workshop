
from langgraph.graph import END
from langgraph.types import Command

from application.use_case.research_agent.models import (
    ResearchAgentState,
)
from core.logging import LogLevel
from domain.enums import BaseEnum
from domain.models import ManagedDocument
from infrastructure.blob_manager import BaseBlobManager
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
        report = self.run(state.goal, state.managed_documents)
        state.research_report = report
        return Command(goto=NextNode.END.value, update=state)

    def run(
        self,
        user_request: str,
        managed_documents: list[ManagedDocument],
        verbose: bool = False,
    ) -> str:
        chain = self._build_chain()
        context="\n\n".join(
            managed_document.to_string()
            for managed_document in managed_documents
        )
        # params = self.blob_manager.read_blob_as_json("storage/prompts/params/gather_requirements.json")
        inputs = {
            "context": context,
            "user_request": user_request,
            # **params,
        }
        return self.invoke(chain, inputs, verbose)



if __name__ == "__main__":
    from core.utils.nano_id import generate_id
    from infrastructure.blob_manager import LocalBlobManager

    blob_manager = LocalBlobManager()
    chain = GenerateReportNode(OpenAIModelName.GPT_5_MINI, blob_manager)

    user_request = "Transformersの論文"
    reading_results = [
        ManagedDocument(
            id=generate_id(),
            task="Transformersの論文",
            paper=ManagedDocument(
                title="Transformersの論文",
                url="https://arxiv.org/abs/2205.01601",
            ),
            url="https://arxiv.org/abs/2205.01601",
            summary="Transformersの論文",
        ),
    ]
    chain.run(user_request, reading_results, verbose=True)
