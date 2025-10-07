from pydantic import BaseModel, Field


class ReadDocumentResult(BaseModel):
    is_related: bool = Field(
        title="タスクとの関連性",
        description="この文書がタスクに関連しているかどうか",
        default=False,
    )
    summary: str = Field(
        title="タスク向け要約",
        description="タスクに対するこの文書の要約",
    )
