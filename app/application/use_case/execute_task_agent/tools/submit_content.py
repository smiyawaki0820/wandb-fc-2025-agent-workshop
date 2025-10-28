from typing import cast, TYPE_CHECKING

from dotenv import load_dotenv
from langchain_core.tools import tool
from openai import OpenAI
from pydantic import BaseModel, Field, computed_field

from app.core.logging import LogLevel
from app.infrastructure.blob_manager import LocalBlobManager

if TYPE_CHECKING:
    from openai.types.responses.parsed_response import ParsedResponse

load_dotenv()


class Submission(BaseModel):
    is_accepted: bool = Field(
        title="提出物の受け入れ判定",
        description="提出物が求められている要件や期待を満たしているかどうかを知らせます。受け入れられた場合は True、要件不足や不備がある場合は False となります。"
    )
    reason: str = Field(
        title="受け入れ判断の詳細理由",
        description=(
            "提出物が受け入れられなかった場合は、どこが要件や期待に達していなかったのか、具体的な改善ポイントやアドバイスを丁寧に記述してください。"
            "逆に、受け入れられた場合は、どの点が要件を満たしていたのか、なぜ十分だったのかについて積極的なフィードバックや称賛を含めて説明してください。"
        ),
        exclude=True
    )

    @computed_field
    @property
    def reason_for_rejection(self) -> str | None:
        return None if self.is_accepted else self.reason


blob_manager = LocalBlobManager(log_level=LogLevel.TRACE)

@tool
def submit_content(content: str) -> dict[str, str | bool | None]:
    """指定された提出物の内容を審査し、受け入れ可否および理由を返します。
    提出物はマークダウン形式で記述してください。本関数は、その内容が所定の要件や期待を満たしているかどうかを判定し、
    判定結果（受け入れ可否）および詳細な理由や改善点（または称賛ポイント）を返します。.

    Args:
    ----
        content (str): マークダウン形式で記述された確認対象の提出物の内容。

    Returns:
    -------
        Submission:
            is_accepted（bool）: 提出物が受け入れ可能かどうか（True: 受け入れ／False: 不可）。
            reason（str）: 受け入れ可否の根拠や詳細な理由。非受理の場合は改善ポイント、受理の場合は称賛コメントなどを含みます。

    """  # noqa: D205
    client = OpenAI()
    system_instruction_template = blob_manager.read_blob_as_template(
        "storage/prompts/research_agent/tools/submit_content.jinja"
    )
    system_instruction = system_instruction_template.render(
        output_format=Submission.model_json_schema()
    )
    result: ParsedResponse[Submission] = client.responses.parse(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": content},
        ],
        text_format=Submission,
        reasoning={ "effort": "low" },
        text={ "verbosity": "low" },
    )
    submission: Submission = cast("Submission", result.output_parsed)
    return submission.model_dump()
