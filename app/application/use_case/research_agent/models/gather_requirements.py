from copy import deepcopy

from pydantic import BaseModel, Field, computed_field

from core.utils.nano_id import generate_id, NanoID
from domain.enums import ManagedTaskStatus, Priority


class ManagedItem(BaseModel):
    id: NanoID = Field(
        title="要件収集項目ID",
        description="このIDは要件収集項目を一意に識別するためのものであり、HTMLフォーム生成時にはinputタグなどのid属性として利用されます。",
    )
    status: ManagedTaskStatus = Field(
        title="要件収集の状況",
        description=(
            "質問に対する回答状況として以下より適切なステータスを選択する:\n"
            "not_started: 未開始\n"
            "completed: 完了\n"
            "pending: 保留/スキップ"
        ),
    )
    answer: str | None = Field(title="ユーザーからの回答")


class ManagedInquiryItem(ManagedItem):
    priority: Priority | None = Field(
        title="優先度",
        description="最適な情報調査を行う上で優先すべき度合いを示す。",
    )
    question: str = Field(title="ユーザーへの確認項目")


class AdditionalQuestion(BaseModel):
    question: str = Field(title="ユーザーへの確認項目")
    priority: Priority | None = Field(
        title="優先度",
        description="最適な情報調査を行う上で優先すべき度合いを示す。",
    )

class GatherRequirements(BaseModel):
    inquiry_items_evaluation: list[ManagedItem] = Field(
        title="既存のInquiryItemに対するステータス評価",
        description="各InquiryItem（要件収集項目）ごとの現在のステータスを示すリスト。",
        default_factory=list,
    )
    additional_questions: list[AdditionalQuestion] = Field(
        title="追加質問",
        description="ユーザーへの確認項目一覧",
        default_factory=list,
        exclude=True,
    )
    skip_gather_requirements: bool | None = Field(
        title="要件収集プロセスをスキップするかどうか",
        description=(
            "この値が True の場合、ユーザーからの情報収集を強制的にスキップします。"
            "ユーザから「そのままの条件で検索し、調査してください。」「/skip」「これ以上の要件収集は不要です」といった回答を得た場合に True としてください。"
        ),
        default=None
    )
    response_to_user: str = Field(
        title="ユーザーへの応答文",
        description="会話履歴を参照し、ユーザーに提示する応答文を生成する",
    )

    @computed_field
    @property
    def inquiry_items(self) -> list[ManagedInquiryItem]:
        return [
            ManagedInquiryItem(
                id=generate_id(),
                priority=item.priority,
                status=ManagedTaskStatus.NOT_STARTED,
                question=item.question,
                answer=None,
            )
            for item in self.additional_questions
        ]

    @computed_field
    @property
    def is_completed(self) -> bool:
        return (
            self.skip_gather_requirements or
            all(
                item.status in (ManagedTaskStatus.COMPLETED, ManagedTaskStatus.PENDING)
                for item in self.inquiry_items
            )
        )

    def update_inquiry_items(self, previous_inquiry_items: list[ManagedInquiryItem]) -> list[ManagedInquiryItem]:
        updated_inquiry_items = deepcopy(previous_inquiry_items)
        for idx, item in enumerate(previous_inquiry_items):
            updated_item = next((e for e in self.inquiry_items_evaluation if e.id == item.id), None)
            if updated_item:
                updated_inquiry_items[idx].status = updated_item.status
                updated_inquiry_items[idx].answer = updated_item.answer
        return updated_inquiry_items
