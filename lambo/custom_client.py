from discord.ext.commands import Bot

from lambo.config import Settings


class CustomClient(Bot):
    settings: Settings

    def __init__(self, settings: Settings, *args, **kwargs):
        prefix = settings.prefix
        super().__init__(command_prefix=prefix, **kwargs)
        self.settings = settings

    async def start(self):
        return await super().start(self.settings.token)

    def run(self):
        return super().run(self.settings.token)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
