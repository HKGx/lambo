from glob import escape
import discord
from discord.ext.commands import Cog, Context, command, group, has_permissions
from lambo.custom_client import CustomClient
from discord.utils import escape_markdown


class UtilitiesCog(Cog):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @command("mentioned")
    async def mentioned(self, ctx: Context, message: discord.Message) -> None:
        users = [escape_markdown(str(user)) for user in message.mentions]
        new_line = "\n"
        str_users = f"```{new_line.join(users)}```"
        await ctx.send(f"{str_users}")


def setup(bot: CustomClient):
    bot.add_cog(UtilitiesCog(bot))
