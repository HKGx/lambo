import math
import typing
from inspect import unwrap
from io import BytesIO

import discord
from discord.ext.commands import Cog, Context, FlagConverter, Greedy, command, flag
from discord.ext.pages import PageGroup, Paginator
from discord.utils import escape_markdown

from lambo import CustomClient
from lambo.utils import FuzzyRoleConverter, codized, quoted, unwrap_channels


class InroleFlags(FlagConverter):
    per_page: int = flag(name="per_page", aliases=["pp", "perpage"], default=20)
    with_ids: bool = flag(name="with_ids", aliases=["ids"], default=True)

    page: int = flag(name="page", default=1)


class ReactedFlags(FlagConverter):
    mentions: bool = flag(name="mentions", aliases=["mention"], default=False)
    hide_names: bool = flag(name="hide_names", aliases=["hide"], default=False)

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
        if not (1 <= flags.per_page <= 30):
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

    @command("searchin")
    async def searchin(
        self,
        ctx: Context,
        _channels: Greedy[discord.abc.GuildChannel],
        prefix: typing.Optional[str] = "in:",
        only_available: typing.Optional[bool] = False,
    ):
        channels: list[discord.abc.GuildChannel] = _channels  # type: ignore
        unwrapped_channels = {
            unwrapped for channel in channels for unwrapped in unwrap_channels(channel)
        }
        if only_available:
            unwrapped_channels = {
                channel for channel in unwrapped_channels if channel.permissions_for(ctx.author).read_messages  # type: ignore
            }

        texts = [f"{prefix}{unwrapped.name}" for unwrapped in unwrapped_channels]
        return await ctx.reply(codized(" ".join(texts)))

    @command("reacted", aliases=["rnr"])
    async def reacted(
        self,
        ctx: Context,
        message: discord.Message,
        role: typing.Optional[discord.Role],
        *,
        flags: ReactedFlags,
    ):
        assert ctx.guild is not None
        assert isinstance(message.channel, discord.abc.GuildChannel)
        members = filter(
            lambda m: not m.bot, role.members if role else message.channel.members
        )
        reacted_users: set[discord.Member] = set()
        reactions_dict: dict[str, list[discord.Member]] = {}
        for reaction in message.reactions:
            users: list[discord.Member] = await (  # type: ignore
                reaction.users(limit=None)
                .filter(lambda user: not user.bot and isinstance(user, discord.Member))
                .flatten()
            )
            reacted_users.update(users)
            emoji_name = (
                reaction.emoji
                if isinstance(reaction.emoji, str)
                else reaction.emoji.name
            )
            reactions_dict[emoji_name] = users
        not_reacted = set(members) - reacted_users

        def format_user(user: discord.Member) -> str:
            if flags.mentions and flags.hide_names:
                return user.mention
            elif flags.mentions:
                return f"{user.mention} ({user})"
            return str(user)

        buffer = ""

        for emoji, users in reactions_dict.items():
            buffer += f"{emoji}: {len(users)}\n"
            for user in users:
                buffer += f"\t{format_user(user)}\n"
        buffer += f"\nNot reacted: {len(not_reacted)}\n"
        for user in not_reacted:
            buffer += f"\t{format_user(user)}\n"

        await ctx.reply(
            file=discord.File(BytesIO(buffer.encode("utf-8")), filename="reacted.txt")
        )


def setup(bot: CustomClient):
    bot.add_cog(UtilitiesCog(bot))
