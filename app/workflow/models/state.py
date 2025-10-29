import operator
from typing import Annotated

from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage

from workflow.models import ManagedInquiryItem
from workflow.models.build_research_plan import (
    ManagedTask,
    ReportSection,
)
from domain.models import ManagedDocument


class ResearchAgentInputState(BaseModel):
    messages: list[AnyMessage] = Field(default_factory=list)


class ResearchAgentPrivateState(BaseModel):
    inquiry_items: list[ManagedInquiryItem] = Field(default_factory=list)
    goal: str = Field(title="goal", default="")
    tasks: list[ManagedTask] = Field(default_factory=list)
    executed_tasks: Annotated[list[ManagedTask], operator.add] = Field(
        default_factory=list
    )
    storyline: list[ReportSection] = Field(default_factory=list)
    managed_documents: Annotated[list[ManagedDocument], operator.add] = Field(
        default_factory=list
    )
    retry_count: int = Field(default=0)


class ResearchAgentOutputState(BaseModel):
    research_report: str | None = Field(
        title="調査レポート",
        description=(
            "本フィールドは、ユーザーから与えられた要求（goal）および収集・分析された文献情報（managed_documents）をもとに、"
            "情報調査エージェントが生成した最終的な調査レポートを格納します。"
            "レポートには、各文献の要約、分析結果、主張の根拠となる引用、発見されたパターンや傾向、"
            "および学術的な厳密さを担保するための適切な引用・参考情報が含まれます。"
            "Markdown形式や表形式など、ユーザーにとって分かりやすい表現も推奨されます。"
            "このレポートは、ユーザーの意思決定や知識獲得を支援するための包括的なアウトプットです。"
        ),
        default=None,
    )


class ResearchAgentState(
    ResearchAgentInputState, ResearchAgentPrivateState, ResearchAgentOutputState
):
    pass
