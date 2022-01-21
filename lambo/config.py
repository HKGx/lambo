from typing import Optional


from pydantic import BaseSettings, Field


def default_extensions():
    return [
        "lambo.cogs.count_emoji",
        "lambo.cogs.moderation_utils",
        "lambo.cogs.utilities",
    ]


class Settings(BaseSettings):
    db_url: str
    prefix: str = "b!"
    extensions: list[str] = Field(default_factory=default_extensions)
    non_default_extensions: list[str] = Field(default_factory=list)
    token: Optional[str] = None
    intents: Optional[list[str]] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
