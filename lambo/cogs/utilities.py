from textwrap import dedent
from tokenize import triple_quoted

import discord
from discord.ext.commands import Cog, Context, command
from discord.ext.pages import PageGroup, Paginator
from discord.utils import escape_markdown
from lambo.custom_client import CustomClient
from lambo.utils import FuzzyRoleConverter


class UtilitiesCog(Cog, name="Utilities"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @command("mentioned")
    async def mentioned(self, ctx: Context, message: discord.Message, with_ids: bool = False) -> None:
        users = [escape_markdown(str(user)) +
                 (f" ({user.id})" if with_ids else "") for user in message.mentions]
        new_line = "\n"
        str_users = f"```{new_line.join(users)}```"
        await ctx.send(f"{str_users}")

    @command("inrole")
    async def inrole(self, ctx: Context, _role: FuzzyRoleConverter, per_page: int = 20, with_ids: bool = True) -> None:
        if per_page not in range(1, 30):
            await ctx.reply("Please enter a number between 1 and 30.")
            return
        role: discord.Role = _role  # type: ignore
        members = []
        for idx, member in enumerate(role.members):
            ordering = f"{(idx + 1):02}. "
            id_str = f"{member.id} " if with_ids else ""
            members.append(f"{ordering}{id_str}{member}")
        # Join every per_page members in one list
        members = ["\n".join(members[i:i + per_page])
                   for i in range(0, len(members), per_page)]
        # Prepend every list with the custom message
        id_str = f" ({role.id})" if with_ids else ""

        prefix = quoted(
            f"Members in role `{role.name}`{id_str}.\n"
            f"Total members: {len(role.members)}.\n")

        members = [f"{prefix}\n{codized(member)}"
                   for member in members]
        paginator = Paginator(pages=members)

        await paginator.send(ctx)


def quoted(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines())


def codized(text: str) -> str:
    return f"```\n{text}\n```"


def setup(bot: CustomClient):
    bot.add_cog(UtilitiesCog(bot))
