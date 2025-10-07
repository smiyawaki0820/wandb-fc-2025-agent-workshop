from application.use_case.execute_task_agent.models import ExecuteTaskAgentState
from core.logging import LogLevel
from infrastructure.llm_chain.base import BaseChain



class ManageTaskNode(BaseChain):
    def __init__(self, log_level: LogLevel = LogLevel.DEBUG) -> None:
        super().__init__(log_level)

    def __call__(self, state: ExecuteTaskAgentState) -> ExecuteTaskAgentState:
        return state
