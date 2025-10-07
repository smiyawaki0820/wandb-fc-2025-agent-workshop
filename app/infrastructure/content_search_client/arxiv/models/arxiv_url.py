from datetime import datetime
from urllib.parse import quote

from pydantic import BaseModel, Field, field_validator


class ArxivSearchParams(BaseModel):
    keywords: list[str] = Field(
        description="List of keywords to be searched (joined with AND condition).",
        default_factory=list,
    )
    start: datetime | None = Field(
        default=None,
        description="The start date of the time range to be retrieved.",
    )
    end: datetime | None = Field(
        default=None, description="The end date of the time range to be retrieved."
    )

    @field_validator("keywords")
    def validate_keywords(cls, v: list[str]) -> list[str]:
        keywords = []
        for keyword in v:
            normalized_keyword = (
                keyword
                .replace('"', "")  # ダブルクオテーションを削除
                .strip()  # 両端の空白を削除
            )
            if normalized_keyword:
                keywords.append(normalized_keyword)
        return keywords


class ArxivUrl(ArxivSearchParams):
    url: str = "https://export.arxiv.org/api/query"
    sort_by: str = "relevance"
    max_results: int = 10

    @classmethod
    def from_params(cls, params: ArxivSearchParams) -> "ArxivUrl":
        return cls(
            keywords=params.keywords,
            start=params.start,
            end=params.end,
        )

    @property
    def search_query(self) -> str:
        return "all:" + " AND ".join(self.keywords)

    @property
    def filter_query(self) -> str:
        start = self.start.strftime("%Y%m%d") if self.start else "EARLIEST"
        end = self.end.strftime("%Y%m%d") if self.end else "LATEST"
        return f"{start}+TO+{end}"

    @property
    def params(self) -> dict:
        return {
            "search_query": quote(self.search_query),
            "sortBy": self.sort_by,
            "max_results": self.max_results,
            "submittedDate": self.filter_query,
        }

    def to_string(self) -> str:
        params = [f"{key}={value}" for key, value in self.params.items() if value]
        return self.url + "?" + "&".join(params)



if __name__ == "__main__":
    arxiv_url = ArxivUrl(keywords=["quantum computing"], max_results=10, start=datetime(2024, 1, 1), end=datetime(2024, 12, 31))
    print(arxiv_url.to_string())
