from dotenv import load_dotenv

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    JINA_API_KEY: str
    OPENAI_API_KEY: str | None = Field(default=None)
    WANDB_API_KEY: str | None = Field(default=None)
    PERPLEXITY_API_KEY: str | None = Field(default=None)

    LOG_LEVEL: str = Field(default="TRACE")
    TIMEZONE: str = Field(default="Asia/Tokyo")
    GLOBAL_INSTRUCTION_PATH: str = Field(
        default="storage/prompts/global_instruction.jinja"
    )


settings = Settings()
