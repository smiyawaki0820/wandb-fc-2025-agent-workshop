from datetime import datetime

from pydantic import Field
from domain.models.document import Document


class ArxivPaper(Document):
    published: datetime = Field(title="公開日")
    updated: datetime = Field(title="更新日")
    version: str | None = Field(title="バージョン", default=None)
    categories: list[str] = Field(title="カテゴリ", default_factory=list)
    relevance_score: float | None = Field(title="関連度スコア", default=None)

    def to_string(self) -> str:
        return f"""\
<paper>
    <id>{self.id}</id>
    <title>{self.title}</title>
    <link>{self.url}</link>
    <abstract>{self.abstract}</abstract>
    <published>{self.published}</published>
    <updated>{self.updated}</updated>
    <version>{self.version}</version>
    <authors>{', '.join(self.authors)}</authors>
    <categories>{', '.join(self.categories)}</categories>
    {f"<relevance_score>{self.relevance_score}</relevance_score>" if self.relevance_score else ""}
</paper>"""
