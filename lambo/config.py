from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    prefix: str = "b!"
    db_url: str
    extensions: list[str] = [
        "lambo.cogs.count_emoji", "lambo.cogs.moderation_utils", "lambo.cogs.utilities"]
    token: str
    intents: Optional[list[str]] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
