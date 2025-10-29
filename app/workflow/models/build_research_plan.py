from pydantic import BaseModel, Field, computed_field

from app.core.utils.datetime_utils import get_current_time
from app.core.utils.nano_id import NanoID, generate_id
from app.domain.enums import BaseEnum, ManagedTaskStatus, Priority


class TaskType(BaseEnum):
    SEARCH = "SEARCH"
    THINKING = "THINKING"
    # CALCULATE = "CALCULATE"  # TODO


class Task(BaseModel):
    title: str = Field(
        title="タスク名",
        description=(
            "タスクを一言で表す名称や見出しを記載してください。"
            "第三者がタスクの内容を簡潔に理解できるようにしてください。"
        ),
    )
    overview: str = Field(
        title="タスク概要",
        description=(
            "このタスクで達成すべき内容や扱うテーマ、その背景など全体像を短くまとめてください。"
            "他のタスクとの関連性や位置付けについても簡単に触れて構いません。"
        ),
    )
    objective: str = Field(
        title="タスクの目的",
        description=(
            "このタスクを行う理由や意図、最終的に得たい成果やゴールを明確に記載します。"
            "なぜこのタスクが必要なのか、実施することでどのような価値が得られるかなども含めてください。"
        ),
    )
    research_scope: str = Field(
        title="調査範囲・スコープ",
        description=(
            "本タスクにおける調査の対象や範囲、深さや制約条件などを具体的に示してください。"
            "調査対象としない事項（アウトオブスコープ）も明示すると明確になります。"
        ),
    )
    priority: Priority = Field(
        title="タスクの優先度",
        description=(
            "このタスクの処理優先度を示します。他タスクと比較してどれだけ早く着手するべきか、"
            "あるいは重要度・緊急度の観点から優先順位を決定する補助としてください。"
        ),
    )
    required_capabilities: list[TaskType] = Field(
        title="要求される能力・タスク種別",
        description=(
            "このタスクを遂行する上で求められる主な能力・活動種別を列挙してください。"
            "例：情報検索（SEARCH）、思考・分析（THINKING）など。"
            "複数該当する場合はリスト形式で記載します。"
        ),
    )


class ManagedTask(Task):
    id: NanoID = Field(title="タスクID")
    status: ManagedTaskStatus = Field(title="タスク状況")
    deliverable: str | None = Field(title="タスクの成果物", default=None)
    created_at: str = Field(default_factory=get_current_time)
    updated_at: str = Field(default_factory=get_current_time)

    @classmethod
    def from_task(cls, task: Task) -> "ManagedTask":
        return ManagedTask(
            id=generate_id(),
            status=ManagedTaskStatus.NOT_STARTED,
            **task.model_dump(),
        )


class ReportSection(BaseModel):
    section: str = Field(
        title="セクション名",
        description=(
            "レポート全体の構成の中で、この章や項目が何を扱うかを正確かつ分かりやすく日本語で記載してください。"
            "例えば『はじめに』『背景』『目的』『手法』『考察』『結論』など、第三者が内容の位置づけや意図を一目で理解できるように明示してください。"
        ),
    )
    description: str = Field(
        title="セクションの説明",
        description=(
            "その章や項目で、どのような情報・視点・データ・論点・検討事項等を扱うかを、具体的に記載してください。"
            "単なる見出しの羅列ではなく、どのポイントをどのように深掘り・解説・比較するかも示してください。"
            "必要に応じて、アウトライン（箇条書き）や要点を交えて分かりやすく整理してください。"
        ),
    )


class ResearchPlan(BaseModel):
    goal: str = Field(
        title="リサーチの目的",
        description=(
            "このリサーチを実施するにあたって、ユーザーが最終的に何を達成したいと考えているのか、どのような意図や背景があるのかを丁寧かつ具体的に記述してください。"
            "単なるキーワードやトピックの羅列ではなく、解決したい課題、知りたい内容、明らかにしたい問いなど、依頼者の視点を踏まえた実現目標をわかりやすく表現してください。"
            "研究の動機や重要性、成果到達後の理想的な姿（理想状態）についても補足できる範囲で盛り込むと望ましいです。"
        ),
    )
    acceptance_criteria: str = Field(
        title="リサーチ成功のためのユーザー意図および受け入れ基準",
        description=(
            "ユーザーの要望や真の意図を的確に把握した上で、調査が成功とみなされる具体的な達成条件や合格基準を明確に記述する。"
            "この基準を満たせばユーザーが納得できるかどうか、第三者視点でも検証可能となるように表現する。"
        ),
    )
    storyline: list[ReportSection] = Field(
        title="ストーリーライン",
        description=(
            "レポートを作成する際に、どのような情報をどの順序でどのような章立てや構成で盛り込むべきかを判断し、セクションごとに書き起こす。"
            "調査の目的・背景・手法・考察など、ユーザーにとって有益なストーリーラインを提案する。"
            "セクションの数はいくらでも構わないが、ユーザーの要望や真の意図を踏まえて最小限に設定してください。"
        ),
    )
    tasks: list[Task] = Field(
        title="調査タスク",
        description=(
            "調査計画を達成するために実施すべき個別の調査タスクを一覧化してください。"
            "各タスクはストーリーライン（storyline）の流れに基づき、主題・概要・目的・調査範囲・優先度を明確に設定すること。"
            "タスク同士はできる限り独立させ、再現可能で具体的なアウトプットを得られる粒度に分解してください。"
        ),
        exclude=True,
    )

    @computed_field
    @property
    def managed_tasks(self) -> list[ManagedTask]:
        return [ManagedTask.from_task(task) for task in self.tasks]

    @computed_field
    @property
    def is_completed(self) -> bool:
        return all(
            managed_task.status
            in [
                ManagedTaskStatus.COMPLETED,
                ManagedTaskStatus.PENDING,
            ]
            for managed_task in self.managed_tasks
        )
