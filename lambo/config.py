from typing import Callable, Optional

from pydantic import BaseSettings, Field


def default_list(*l: str) -> Callable[[], list[str]]:
    return lambda: list(l)


class Settings(BaseSettings):
    prefix: str = "b!"
    db_url: str = "sqlite://:memory:"
    extensions: list[str] = Field(default_factory=default_list("lambo.cogs"))
    models: list[str] = Field(default_factory=default_list("lambo.models"))
    non_default_extensions: list[str] = Field(default_factory=list)
    non_default_models: list[str] = Field(default_factory=list)
    token: Optional[str] = None
    intents: list[str] = Field(
        default_factory=default_list(
            "emojis",
            "reactions",
            "guild_messages",
            "guilds",
            "members",
            "message_content",
        )
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
