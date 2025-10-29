from pydantic import BaseModel, Field

from workflow.models.build_research_plan import (
    Task,
    ManagedTask,
)


class ExecuteTaskState(BaseModel):
    goal: str | None = Field(title="goal", default=None)
    task: ManagedTask = Field(title="task")


class TaskExecution(BaseModel):
    deliverable: str | None = Field(title="提出物", default=None)
    additional_tasks: list[Task] = Field(
        title="追加タスク",
        description="目的達成のためにタスクを追加すべきである場合は新たにタスクを定義し、そのタスクを追加する。",
        default_factory=list,
    )
