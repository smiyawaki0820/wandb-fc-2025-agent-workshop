from pydantic import BaseModel, Field

from application.use_case.research_agent.models import ManagedTask
from domain.models import ManagedDocument


class ExecuteTaskAgentInputState(BaseModel):
    goal: str | None = Field(title="goal", default=None)
    task: ManagedTask = Field(title="task")


class ExecuteTaskAgentOutputState(BaseModel):
    managed_documents: list[ManagedDocument] = Field(default_factory=list)


class ExecuteTaskAgentState(
    ExecuteTaskAgentInputState,
    ExecuteTaskAgentOutputState,
):
    pass
