from pydantic import BaseModel, Field

from domain.enums import TaskStatus
from application.use_case.research_agent.models import Task


class TaskCriteriaFulfillmentEvaluation(BaseModel):
    task_id: str = Field(title="タスクID")
    status: TaskStatus = Field(title="タスク状況")
    overall_evaluation: str = Field(
        title="総合評価と根拠の詳細",
        description="reading_resultsを踏まえた総合的な評価、評価の妥当性、判断理由を日本語で分かりやすく記載する。評価の根拠や考慮した観点も具体的に明示する。"
    )
    reconstructed_task: Task | None = Field(
        title="再定義されたタスク",
        description="目的達成のためにタスクの内容や条件を見直す必要がある場合に、Taskを再構成したものを記載する。タスクの再定義が必要と判断された場合のみ入力する。"
    )


class TaskEvaluation(BaseModel):
    criteria_evals: list[TaskCriteriaFulfillmentEvaluation] = Field(
        title="達成基準評価",
        description="与えられたタスクそれぞれについて、その達成基準が達成されているかどうかを評価する。"
    )
    additional_tasks: list[Task] = Field(
        title="追加タスク",
        description="目的達成のためにタスクを追加すべきである場合は新たにタスクを定義する。",
        default_factory=list,
    )
