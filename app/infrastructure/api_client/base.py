from functools import partial

import feedparser
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.exception import ApiClientError
from core.logging import LogLevel, log


class BaseApiClient:
    def __init__(self, log_level: LogLevel) -> None:
        self.log = partial(log, log_level=log_level, subject=self.__name__)
        self.client = httpx.Client()

    @property
    def __name__(self) -> str:
        return str(self.__class__.__name__)

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def post(
        self,
        url: str,
        headers: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        response = self.client.post(url, headers=headers, json=data)
        if response.status_code != 200:
            raise ApiClientError(self.__name__, response.status_code, response.text)
        return response.json()

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
            raise ApiClientError(self.__name__, response.status_code, response.text)

        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        return {"content": response.text}

    def parse_rssfeed(self, url: str) -> list[feedparser.FeedParserDict]:
        feed = feedparser.parse(url)
        return feed.entries
