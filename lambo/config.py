from pydantic import BaseSettings


class Settings(BaseSettings):
    prefix: str = "b!"
    db_url: str
    extensions: list[str] = []
    token: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
