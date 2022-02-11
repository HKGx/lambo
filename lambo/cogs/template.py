import discord
from discord.ext.commands import Cog, Context, command
from discord.utils import escape_markdown
from lambo import CustomClient


class TemplateCog(Cog, name="Template"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot


def setup(bot: CustomClient):
    bot.add_cog(TemplateCog(bot))
