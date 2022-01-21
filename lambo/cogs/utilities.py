import math
from textwrap import dedent
from tokenize import triple_quoted

import discord
from discord.ext.commands import Cog, Context, command, FlagConverter, flag
from discord.ext.pages import PageGroup, Paginator
from discord.utils import escape_markdown
from lambo.custom_client import CustomClient
from lambo.utils import FuzzyRoleConverter


class InroleFlags(FlagConverter):
    per_page: int = flag(name="per_page", aliases=["pp", "perpage"], default=20)
    with_ids: bool = flag(name="with_ids", aliases=["ids"], default=True)

    page: int = flag(name="page", default=1)


class UtilitiesCog(Cog, name="Utilities"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @command("mentioned")
    async def mentioned(
        self, ctx: Context, message: discord.Message, with_ids: bool = False
    ) -> None:
        users = [
            escape_markdown(str(user)) + (f" ({user.id})" if with_ids else "")
            for user in message.mentions
        ]
        new_line = "\n"
        str_users = f"```{new_line.join(users)}```"
        await ctx.send(f"{str_users}")

    @command("inrole")
    async def inrole(
        self, ctx: Context, _role: FuzzyRoleConverter, *, flags: InroleFlags
    ) -> None:
        if not 1 <= flags.per_page <= 30:
            await ctx.reply("Please enter a number between 1 and 30.")
            return
        role: discord.Role = _role  # type: ignore
        members = []
        pad_with = math.floor(math.log10(min(len(role.members), 1000))) + 1
        for idx, member in enumerate(role.members[:1000]):
            ordering = f"{(idx + 1):0{pad_with}}. "
            id_str = f"{member.id} " if flags.with_ids else ""
            members.append(f"{ordering}{id_str}{member}")
        # Join every per_page members in one list
        members_pages = [
            "\n".join(members[i : i + flags.per_page])
            for i in range(0, len(members), flags.per_page)
        ]
        # Prepend every list with the custom message
        id_str = f" ({role.id})" if flags.with_ids else ""

        prefix = (
            f"Members in role `{role.name}`{id_str}.\n"
            f"Total members: {len(role.members)}.\n"
        )
        length_disclaimer = (
            f"Showing only first 1000 members.\n" if len(role.members) > 1000 else ""
        )

        prefix += length_disclaimer
        prefix = quoted(prefix)
        members_pages = [f"{prefix}\n{codized(page)}" for page in members_pages]
        if flags.page not in range(1, len(members_pages) + 1):
            await ctx.reply(
                f"That page does not exist. Please specify page between 1 and {len(members_pages)}."
            )
            return
        paginator = Paginator(pages=members_pages)
        paginator.current_page = flags.page - 1

        await paginator.send(ctx)

    @command("reload")
    @discord.is_owner()
    async def reload(self, ctx: Context[CustomClient]) -> None:
        async with ctx.typing():
            for extension in list(ctx.bot.extensions.keys()):
                ctx.bot.reload_extension(extension)
        await ctx.reply("Reloaded all extensions.")


def quoted(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines())


def codized(text: str) -> str:
    return f"```\n{text}\n```"


def setup(bot: CustomClient):
    bot.add_cog(UtilitiesCog(bot))
