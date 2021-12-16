import discord
from discord.ext.commands import Cog, Context, command
from discord.utils import escape_markdown
from lambo.custom_client import CustomClient


class UtilitiesCog(Cog, name="Utilities"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @command("mentioned")
    async def mentioned(self, ctx: Context, message: discord.Message, with_ids: bool = None) -> None:
        if with_ids is None:
            with_ids = False
        users = [escape_markdown(str(user)) +
                 (f" ({user.id})" if with_ids else "") for user in message.mentions]
        new_line = "\n"
        str_users = f"```{new_line.join(users)}```"
        await ctx.send(f"{str_users}")


def setup(bot: CustomClient):
    bot.add_cog(UtilitiesCog(bot))
