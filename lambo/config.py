from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    prefix: str = "b!"
    db_url: str
    extensions: list[str] = [
        "lambo.cogs.count_emoji",
        "lambo.cogs.moderation_utils",
        "lambo.cogs.utilities",
    ]
    models: list[str] = ["lambo.models.used_emoji_model"]
    non_default_extensions: list[str] = []
    token: Optional[str] = None
    intents: Optional[list[str]] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
