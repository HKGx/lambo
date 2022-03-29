from typing import Optional
import discord
from discord.cog import Cog
from discord.ext.commands import Bot, when_mentioned_or
from logging import Logger, getLogger, StreamHandler, DEBUG, BASIC_FORMAT, Formatter
from lambo.config import Settings


LOGGER_FORMAT = "[%(levelname)s][%(asctime)s][%(name)s]: %(message)s"


class CustomClient(Bot):
    _settings: Settings
    _logger: Logger = getLogger("lambo")

    @property
    def logger(self) -> Logger:
        return self._logger

    def __init__(self, settings: Settings, *args, **kwargs):

        prefix = settings.prefix
        raw_intents = settings.intents
        intents = discord.Intents.none()

        if raw_intents is None:
            intents = discord.Intents.default()
        else:
            valid_intents: dict[str, int] = discord.Intents.VALID_FLAGS  # type: ignore # noqa
            for intent in raw_intents:
                if intent not in valid_intents:
                    raise ValueError(f"Invalid intent: {intent}")
                setattr(intents, intent, True)

        self._settings = settings
        self.logger.setLevel(DEBUG)
        handler = StreamHandler()
        handler.setFormatter(Formatter(LOGGER_FORMAT))
        self.logger.addHandler(handler)

        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True

        super().__init__(
            command_prefix=when_mentioned_or(prefix),
            intents=intents,
            allowed_mentions=allowed_mentions,
            **kwargs,
        )

    async def start(self):
        if self._settings.token is None:
            raise ValueError("No token provided")
        return await super().start(self._settings.token)

    def add_cog(self, cog: Cog, *, override: bool = False) -> None:
        self.logger.info(f"Adding cog `{cog.qualified_name}`")
        return super().add_cog(cog, override=override)

    def remove_cog(self, name: str) -> Optional[Cog]:
        value = super().remove_cog(name)
        if value is not None:
            self.logger.info(f"Removed cog `{value.qualified_name}`")
        return value

    def load_extension(self, name: str, *, package: Optional[str] = None) -> None:
        self.logger.info(f"Loading extension `{name}`")
        return super().load_extension(name, package=package)

    def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        self.logger.info(f"Unloading extension `{name}`")
        return super().unload_extension(name, package=package)

    def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        self.logger.info(f"Reloading extension `{name}`")
        return super().reload_extension(name, package=package)

    def run(self):
        return super().run(self._settings.token)

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} with intents {self.intents}")
