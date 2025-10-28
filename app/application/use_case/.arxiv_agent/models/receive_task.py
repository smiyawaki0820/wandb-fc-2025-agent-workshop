from pydantic import BaseModel, Field

from core.utils.nano_id import NanoID
from domain.enums import ManagedTaskStatus
from domain.models import ManagedDocument



class ReceiveTaskExecution(BaseModel):
    need_research: bool = Field(
        title="ドキュメント調査の必要性",
        description="外部知識資源（WEBページや社内ドキュメントなど）への調査が必要なタスクである場合は True とする。",
        default=False,
    )
    task_response: str | None = Field(
        title="タスクの回答",
        description="調査が不要なタスクにおいて、その回答を生成する。",
        default=None,
    )


class ManagedTaskExecution(ReceiveTaskExecution):
    id: NanoID = Field(title="タスク実行ID")
    status: ManagedTaskStatus = Field(title="タスク実行状況")
    managed_documents: list[ManagedDocument] = Field(title="管理文書", default_factory=list)

