from logging import (BASIC_FORMAT, DEBUG, Formatter, Handler, Logger,
                     StreamHandler, getLogger)
from typing import Optional

import discord
from discord.ext.commands import Bot, Cog, when_mentioned_or
from psycopg import AsyncConnection

from lambo.settings import Settings

LOGGER_FORMAT = "[%(levelname)s][%(asctime)s][%(name)s]: %(message)s"


class CustomClient(Bot):
    _settings: Settings
    _connection: AsyncConnection

    def __init__(self, settings: Settings, **kwargs):

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

        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True

        super().__init__(
            command_prefix=when_mentioned_or(prefix),
            intents=intents,
            allowed_mentions=allowed_mentions,
            **kwargs,
        )

    @property
    def db(self):
        return self._connection.cursor()

    async def setup_hook(self) -> None:
        self._connection = await AsyncConnection.connect(self._settings.db_url)

    async def start(self):
        if self._settings.token is None:
            raise ValueError("No token provided")
        return await super().start(self._settings.token)

    async def add_cog(self, cog: Cog, *, override: bool = False) -> None:
        # self.logger.info(f"Adding cog `{cog.qualified_name}`")
        return await super().add_cog(cog, override=override)

    async def remove_cog(self, name: str) -> Optional[Cog]:
        value = await super().remove_cog(name)
        # if value is not None:
        #     self.logger.info(f"Removed cog `{value.qualified_name}`")
        return value

    async def load_extension(self, name: str, *, package: Optional[str] = None) -> None:
        # self.logger.info(f"Loading extension `{name}`")
        return await super().load_extension(name, package=package)

    async def unload_extension(
        self, name: str, *, package: Optional[str] = None
    ) -> None:
        # self.logger.info(f"Unloading extension `{name}`")
        return await super().unload_extension(name, package=package)

    async def reload_extension(
        self, name: str, *, package: Optional[str] = None
    ) -> None:
        # self.logger.info(f"Reloading extension `{name}`")
        return await super().reload_extension(name, package=package)

    def run(self):
        raise DeprecationWarning("Please use asynchrounous `.start`!")

    async def on_ready(self):
        pass
        # self.logger.info(f"Logged in as {self.user} with intents {self.intents}")
