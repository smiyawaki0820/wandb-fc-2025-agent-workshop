from dotenv import load_dotenv
from perplexity import Perplexity

from core.config import settings
from core.logging import LogLevel
from core.utils.nano_id import generate_id
from domain.models import Document
from infrastructure.content_search_client.base import BaseContentSearchClient
from infrastructure.content_search_client.perplexity.models import SearchResult


load_dotenv()

class PerplexitySearchClient(BaseContentSearchClient):
    def __init__(
        self,
        log_level: LogLevel,
        api_key: str = settings.PERPLEXITY_API_KEY,
    ) -> None:
        self.client = Perplexity(api_key=api_key)
        super().__init__(log_level)

    def search(self, user_request: str) -> list[Document]:
        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_request
                }
            ],
            model="sonar",
        )
        documents = []
        for res in completion.search_results:
            search_result = SearchResult.model_validate(res.model_dump())
            documents.append(
                Document(
                    id=generate_id(),
                    title=search_result.title,
                    url=search_result.url,
                    abstract=search_result.snippet,
                    authors=[search_result.source],
                )
            )
        return documents



if __name__ == "__main__":
    client = PerplexitySearchClient(log_level=LogLevel.DEBUG)
    documents = client.search("Transformerの論文")
    for document in documents:
        print(document.title)
        print(document.url)
        print(document.abstract)
        print(document.authors)
        print("-" * 100)

