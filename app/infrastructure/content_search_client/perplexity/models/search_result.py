from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    date: str | None = None
    last_updated: str | None = None
    snippet: str | None = None
    source: str | None = None
