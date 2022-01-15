import discord
from discord.ext.commands import Bot, when_mentioned_or

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
        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True
        super().__init__(command_prefix=when_mentioned_or(prefix),
                         intents=intents, allowed_mentions=allowed_mentions, **kwargs)
        self.settings = settings

    async def start(self):
        if self.settings.token is None:
            raise ValueError("No token provided")
        return await super().start(self.settings.token)

    def run(self):
        return super().run(self.settings.token)

    async def on_ready(self):
        print(
            f'Logged in as {self.user} with intents {self.intents}', flush=True)
