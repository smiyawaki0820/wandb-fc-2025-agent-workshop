from pydantic import BaseModel, Field, computed_field

from core.utils.datetime_utils import get_current_time
from core.utils.nano_id import NanoID, generate_id
from domain.enums import ManagedTaskStatus, Priority


class Task(BaseModel):
    subject: str = Field(title="タスクの主題")
    summary: str = Field(title="タスクの概要")
    purpose: str = Field(title="タスクの目的")
    scope: str = Field(title="調査範囲")
    priority: Priority = Field(title="タスクの優先度")


class ManagedTask(Task):
    id: NanoID = Field(title="タスクID")
    status: ManagedTaskStatus = Field(title="タスク状況")
    created_at: str = Field(default_factory=get_current_time)
    updated_at: str = Field(default_factory=get_current_time)


class ResearchPlan(BaseModel):
    purpose: str = Field(title="調査目的")
    tasks: list[Task] = Field(title="調査タスク", exclude=True)
    report_contents: list[str] = Field(title="レポートに含めるべき内容")

    @computed_field
    @property
    def managed_tasks(self) -> list[ManagedTask]:
        return [
            ManagedTask(
                id=generate_id(),
                status=ManagedTaskStatus.NOT_STARTED,
                subject=task.subject,
                summary=task.summary,
                purpose=task.purpose,
                scope=task.scope,
                priority=task.priority,
            )
            for task in self.tasks
        ]

    @computed_field
    @property
    def is_completed(self) -> bool:
        return all(
            managed_task.status == ManagedTaskStatus.COMPLETED
            for managed_task in self.managed_tasks
        )
