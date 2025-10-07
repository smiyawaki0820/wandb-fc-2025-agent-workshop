import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from urllib.parse import quote

from core.exception import ApiClientError
from core.logging import LogLevel
from infrastructure.pdf_converter.base import BasePdfReader


class JinaPdfReader(BasePdfReader):
    BASE_URL = "https://r.jina.ai"

    def __init__(
        self,
        api_key: str,
        log_level: LogLevel = LogLevel.DEBUG,
    ) -> None:
        self.headers = {"Authorization": f"Bearer {api_key}"}
        super().__init__(log_level)

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def get(
        self,
        url: str,
        headers: dict | None = None,
    ) -> dict:
        response = self.client.get(url, headers=headers)
        if response.status_code != 200:
            raise ApiClientError(self.service_name, response.status_code, response.text)
        return response.json()

    def convert(self, url: str) -> str:
        encoded_url = quote(url, safe="")
        jina_url = f"{self.BASE_URL}/{encoded_url}"
        return self.get(jina_url, headers=self.headers)
