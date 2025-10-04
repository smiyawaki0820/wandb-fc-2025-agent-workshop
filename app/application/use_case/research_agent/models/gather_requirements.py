from copy import deepcopy

from pydantic import BaseModel, Field, computed_field
from ulid import ULID

from domain.enums import ManagedTaskStatus


class ManagedItem(BaseModel):
    id: str = Field(title="要件収集項目ID")
    status: ManagedTaskStatus = Field(title="要件収集の状況")
    answer: str | None = Field(title="ユーザーからの回答")


class ManagedInquiryItem(ManagedItem):
    question: str = Field(title="ユーザーへの確認項目")


class GatherRequirements(BaseModel):
    inquiry_items_evaluation: list[ManagedItem] = Field(
        title="既存のInquiryItemに対するステータス評価",
        description="各InquiryItem（要件収集項目）ごとの現在のステータスを示すリスト。",
        default_factory=list,
    )
    additional_questions: list[str] = Field(
        title="追加質問",
        description="ユーザーへの確認項目一覧",
        default_factory=list,
        exclude=True,
    )

    @computed_field
    @property
    def inquiry_items(self) -> list[ManagedInquiryItem]:
        return [
            ManagedInquiryItem(
                id=str(ULID()),
                status=ManagedTaskStatus.NOT_STARTED,
                question=question,
                answer=None,
            )
            for question in self.additional_questions
        ]

    def update_inquiry_items(self, previous_inquiry_items: list[ManagedInquiryItem]) -> list[ManagedInquiryItem]:
        updated_inquiry_items = deepcopy(previous_inquiry_items)
        for idx, item in enumerate(previous_inquiry_items):
            updated_item = next((e for e in self.inquiry_items_evaluation if e.id == item.id), None)
            if updated_item:
                updated_inquiry_items[idx].status = updated_item.status
                updated_inquiry_items[idx].answer = updated_item.answer
        return updated_inquiry_items
