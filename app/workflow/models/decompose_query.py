from pydantic import BaseModel, Field


class DecomposedTasks(BaseModel):
    tasks: list[str] = Field(
        title="tasks",
        description="分解されたタスクのリスト",
        default_factory=list,
        min_length=3,
        max_length=5,
    )
