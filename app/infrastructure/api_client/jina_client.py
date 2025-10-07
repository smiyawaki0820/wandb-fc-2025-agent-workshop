from urllib.parse import quote

from core.config import settings
from core.logging import LogLevel
from infrastructure.api_client.base import BaseApiClient


class JinaClient(BaseApiClient):
    BASE_URL = "https://r.jina.ai"

    def __init__(
        self,
        api_key: str = settings.JINA_API_KEY,
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        self.headers = {"Authorization": f"Bearer {api_key}"}
        super().__init__(log_level=log_level)

    def pdf_to_markdown(self, pdf_url: str) -> dict | None:
        encoded_url = quote(pdf_url, safe="")
        jina_url = f"{self.BASE_URL}/{encoded_url}"
        try:
            return self.get(jina_url, headers=self.headers)
        except Exception as e:
            return None


if __name__ == "__main__":
    jina_client = JinaClient()
    markdown = jina_client.pdf_to_markdown("https://arxiv.org/pdf/2203.00001.pdf")
    print(markdown)
