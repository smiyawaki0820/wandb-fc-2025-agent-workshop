from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel

from infrastructure.api_client import BaseApiClient
from core.config import settings
from core.logging import LogLevel
from core.utils.datetime_utils import get_current_time
from infrastructure.blob_manager import BaseBlobManager
from infrastructure.content_search_client.base import BaseContentSearchClient
from infrastructure.content_search_client.arxiv.models import (
    ArxivPaper, ArxivSearchParams, ArxivUrl,
)
from infrastructure.llm_chain.enums import OpenAIModelName


class ArxivSearchClient(BaseContentSearchClient):
    def __init__(
        self,
        blob_manager: BaseBlobManager,
        model_name: OpenAIModelName = OpenAIModelName.GPT_5_NANO,
        prompt_path: str = "storage/prompts/arxiv_search_client/build_search_query.jinja",
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        self.blob_manager = blob_manager
        self.model_name = model_name
        self.prompt_path = prompt_path
        self.api_client = BaseApiClient(log_level=log_level)
        super().__init__(log_level)

    @property
    def global_instruction(self) -> str:
        template = self.blob_manager.read_blob_as_template(settings.GLOBAL_INSTRUCTION_PATH)
        return template.render(current_date=get_current_time())

    def _build_structured_chain(
        self,
        schema: BaseModel,
        temperature: float = 0.0,
    ) -> RunnableSequence:
        llm = ChatOpenAI(model_name=self.model_name.value, temperature=temperature)
        template = self.blob_manager.read_blob_as_str(self.prompt_path)
        prompt = ChatPromptTemplate.from_template(template, template_format="jinja2")
        return prompt | llm.with_structured_output(schema, method="function_calling")  # type: ignore

    def _build_search_query(self, user_request: str) -> ArxivSearchParams:
        chain = self._build_structured_chain(ArxivSearchParams)
        inputs = {
            "global_instruction": self.global_instruction,
            "user_request": user_request,
            "output_format": ArxivSearchParams.model_json_schema(),
        }
        return chain.invoke(inputs)

    def search(self, user_request: str) -> list[ArxivPaper]:
        arxiv_search_params = self._build_search_query(user_request)
        self.log(object="search", message=f"arxiv_search_params: {arxiv_search_params.model_dump_json(indent=2)}")
        arxiv_url = ArxivUrl.from_params(arxiv_search_params)
        url = arxiv_url.to_string()
        self.log(object="search", message=f"arxiv_url: {url}")
        entries = self.api_client.parse_rssfeed(url)
        arxiv_papers = []
        for entry in entries:
            id_ = entry.id.split("/")[-1].split("v")[0]
            version = entry.id.split("/")[-1].split("v")[-1]
            pdf_link = next(
                (
                    link.href
                    for link in entry.links
                    if link.type == "application/pdf"
                ),
                "",
            )
            published = datetime(*entry.published_parsed[:6])  # noqa: DTZ001
            updated = datetime(*entry.updated_parsed[:6])  # noqa: DTZ001
            authors = [author.get("name", "") for author in entry.get("authors", [])]
            categories = [tag.get("term", "") for tag in entry.get("tags", [])]
            arxiv_paper = ArxivPaper(
                id=id_,
                title=entry.title,
                url=entry.link,
                pdf_link=pdf_link,
                abstract=entry.summary,
                published=published,
                updated=updated,
                version=version,
                authors=authors,
                categories=categories,
            )
            arxiv_papers.append(arxiv_paper)
        return arxiv_papers



if __name__ == "__main__":
    from infrastructure.blob_manager.local import LocalBlobManager

    blob_manager = LocalBlobManager()
    reader = ArxivSearchClient(blob_manager)
    papers = reader.search(user_request=(
        "シーンテキストを含むテキスト画像検索の総説・サーベイ論文を網羅的に収集して要点を整理する"
    ))
    print(papers)
    import ipdb; ipdb.set_trace()
