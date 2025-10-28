import json
from functools import partial

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field

from app.application.use_case.execute_task_agent.tools import search_web, submit_content
from app.core.middleware import handle_tool_errors, validate_output
from app.domain.enums import TaskStatus
from app.application.use_case.research_agent.models import Task
from app.infrastructure.blob_manager import LocalBlobManager
from app.core.logging import LogLevel


load_dotenv()

blob_manager = LocalBlobManager(log_level=LogLevel.TRACE)


example_plan = {
    "subject": "採用プロセスにおけるAIエージェント活用のユースケース候補の洗い出しと評価指標の設定",
    "summary": "候補となるユースケースを列挙し、導入効果を評価する指標を設定する。",
    "purpose": "実装意思決定を支援する具体的なユースケースを提示する。",
    "scope": "日本市場の採用BPO領域でのAIエージェント活用ユースケース",
}
system_prompt = (
    "あなたは優秀なリサーチアシスタントです。"
    "このプロジェクトでは最終的に、採用プロセスにおけるAIエージェント活用の調査レポートをまとめることを目的としています。"
    "本タスクではその一部として、特定の観点に絞った調査サブタスクを行います。"
    "与えられた観点について必要な情報を分かりやすく整理・調査し、調査結果と今後深掘りすべき点を丁寧に報告してください。"
    "最終的にツールの submit_content を使用して、調査結果を提出してください。"
)


class TaskExecutionOutput(BaseModel):
    deliverable: str = Field(title="提出物")
    status: TaskStatus = Field(title="タスクの状況")
    additional_tasks: list[Task] = Field(
        title="追加タスク",
        description="目的達成のためにタスクを追加すべきである場合は新たにタスクを定義し、そのタスクを追加する。",
        default_factory=list,
    )


graph = create_agent(
    model="openai:gpt-5-nano",
    tools=[search_web, submit_content],
    system_prompt=blob_manager.read_blob_as_str(
        "storage/prompts/research_agent/nodes/execute_task.jinja"),
    middleware=[
        handle_tool_errors,
        validate_output,
    ],
    # response_format=ToolStrategy(TaskExecutionOutput)
).with_config({"recursion_limit": 50})
inputs = {
    "messages": [
        {"role": "user", "content": json.dumps(example_plan, ensure_ascii=False)}
    ]
}
res = graph.invoke({})
print(res)
import ipdb; ipdb.set_trace()
