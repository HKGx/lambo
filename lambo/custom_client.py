import discord
from discord.ext.commands import Bot

from lambo.config import Settings


class CustomClient(Bot):
    settings: Settings

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
                    raise ValueError(f'Invalid intent: {intent}')
                setattr(intents, intent, True)

        print(f'Intents: {intents}')
        super().__init__(command_prefix=prefix, intents=intents, **kwargs)
        self.settings = settings

    async def start(self):
        return await super().start(self.settings.token)

    def run(self):
        return super().run(self.settings.token)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
