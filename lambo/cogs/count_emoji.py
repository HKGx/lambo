from datetime import datetime
from typing import Generator

import discord
from discord.ext.commands import Cog, Context, group, is_owner
from discord.utils import DISCORD_EPOCH
from lambo.custom_client import CustomClient
from lambo.utils import DateConverter
from prisma.models import EmojiSent
from prisma.types import EmojiSentCreateInput

_EPOCH = datetime.utcfromtimestamp(DISCORD_EPOCH / 1000)


def get_guild_emojis_from_str(string: str, guild: discord.Guild) -> set[int]:
    emojis = set()
    for emoji in guild.emojis:
        if str(emoji) in string:
            emojis.add(emoji.id)
    return emojis


def parse_message(message: discord.Message) -> list[EmojiSentCreateInput]:
    if message.guild is None:
        # Ignore DM messages
        return []
    emojis = get_guild_emojis_from_str(message.content, message.guild)
    """
    emoji_id: int
    user_id: int
    guild_id: int
    channel_id: int
    """
    return [
        EmojiSentCreateInput(
            emoji_id=str(emoji),
            user_id=str(message.author.id),
            guild_id=str(message.guild.id),
            channel_id=str(message.channel.id),
        )
        for emoji in emojis
    ]


class CountEmojiCog(Cog, name="Emoji Counting"):
    bot: CustomClient

    def __init__(self, bot: CustomClient):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        prefixes = await self.bot.get_prefix(message)
        if any(message.content.startswith(prefix) for prefix in prefixes):
            return
        parsed_emojis = parse_message(message)
        await EmojiSent.prisma().create_many(data=parsed_emojis)

    @group(name="emojis")
    async def emojis(self, ctx: Context):
        pass

    @emojis.command(name="count", aliases=("c",))
    async def emojis_count(
        self,
        ctx: Context,
        emoji: discord.Emoji,
        from_date: DateConverter = None,
        to_date: DateConverter = None,
    ):
        if emoji.guild is None:
            await ctx.send("This emoji is not in a guild.")
            return
        from_: datetime = from_date or _EPOCH  # type: ignore
        to_: datetime = to_date or datetime.now()  # type: ignore
        from_ = from_.replace(hour=0, minute=0, second=0)
        emojis_count = await EmojiSent.prisma().count(
            where={
                "guild_id": str(emoji.guild.id),
                "emoji_id": str(emoji.id),
                "sent_at": {"gte": from_, "lte": to_},
            }
        )
        from_str = discord.utils.format_dt(from_)
        to_str = discord.utils.format_dt(to_)
        await ctx.send(
            f"{emoji} was used {emojis_count} times from {from_str} to {to_str}."
        )

    # TODO: Reimplement `emojis_users` with prisma
    # Regression - waiting for https://github.com/RobertCraigie/prisma-client-py/issues/28
    # Could implement this with raw SQL queries, but that's dumb

    # @emojis.command(name="users", aliases=("u",))
    # async def emojis_users(self, ctx: Context, emoji: discord.Emoji, from_date: DateConverter = None, to_date: DateConverter = None):
    #     if emoji.guild is None:
    #         await ctx.send("This emoji is not in a guild.")
    #         return
    #     from_: datetime = datetime.combine(
    #         from_date, datetime.min.time()) if from_date is not None else _EPOCH  # type: ignore
    #     to_: datetime = datetime.combine(
    #         to_date, datetime.max.time()) if to_date is not None else datetime.now()  # type: ignore
    #     # Get all users who used the emoji and their count
    #     users: list[dict[str, int]] = (
    #         await UsedEmojiModel
    #         .annotate(count=Count("used_by"))
    #         .group_by("used_by")
    #         .order_by("-count")
    #         .filter(
    #             emoji=emoji.name,
    #             timestamp__gte=from_,
    #             timestamp__lte=to_
    #         ).limit(10)
    #         .values("used_by", "count")  # type: ignore
    #     )
    #     # All usages during the time period
    #     emojis_count = await UsedEmojiModel.filter(
    #         emoji=emoji.name, timestamp__gte=from_, timestamp__lte=to_).count()
    #     from_str = get_timestamp_tag(from_)
    #     to_str = get_timestamp_tag(to_)
    #     sb = f"{emoji} user usages from {from_str} to {to_str}."
    #     for user in users:
    #         percentage = round(user["count"] / emojis_count * 100, 2)
    #         sb += f"\n<@{user['used_by']}> used {user['count']} times ({percentage}%)."
    #     await ctx.send(sb, allowed_mentions=discord.AllowedMentions(users=False))

    # TODO: Reimplement `emojis_rank` with prisma
    # Regression - waiting for https://github.com/RobertCraigie/prisma-client-py/issues/28\
    # Could implement this with raw SQL queries, but that's dumb

    # @emojis.command(name="rank", aliases=("r", "ranking"))
    # async def emojis_rank(self, ctx: Context, from_date: DateConverter = None, to_date: DateConverter = None):
    #     from_: datetime = datetime.combine(
    #         from_date, datetime.min.time()) if from_date is not None else _EPOCH  # type: ignore
    #     to_: datetime = datetime.combine(
    #         to_date, datetime.max.time()) if to_date is not None else datetime.now()  # type: ignore
    #     values: list[dict[str, int | str]] = (await UsedEmojiModel.annotate(count=Count("id"))  # type: ignore
    #                                           .filter(timestamp__gte=from_, timestamp__lte=to_)
    #                                           .limit(10)
    #                                           .group_by("emoji")
    #                                           .order_by("-count")
    #                                           .values("emoji", "count"))
    #     from_str = get_timestamp_tag(from_)
    #     to_str = get_timestamp_tag(to_)
    #     content = f"Ranking from {from_str} to {to_str}\n"
    #     guild: discord.Guild = ctx.guild  # type: ignore
    #     assert isinstance(guild, discord.Guild)
    #     for g in values:
    #         guild_emojis: tuple[discord.Emoji, ...] = guild.emojis
    #         emojis: list[discord.Emoji] = [
    #             e for e in guild_emojis if e.name == g["emoji"]
    #         ]
    #         if len(emojis) == 0:
    #             continue
    #         emoji: discord.Emoji = emojis[0]
    #         content += f"{emoji} was used {g['count']} times.\n"
    #     await ctx.send(content)

    @is_owner()
    @emojis.command(name="load-history", hidden=True)
    async def load_history(
        self, ctx: Context, limit: int, before: discord.Message = None
    ):
        before_message: discord.Message = before if before is not None else ctx.message  # type: ignore
        limit = min(limit, 10000)
        await ctx.send("Loading history...")
        i = 0
        last = before_message
        async with ctx.typing():
            async for message in ctx.channel.history(
                limit=limit, before=before_message
            ):
                if message.author.bot:
                    continue
                if message.content.startswith(self.bot.command_prefix):
                    continue
                parsed_emojis = parse_message(message)
                await EmojiSent.prisma().create_many(data=parsed_emojis)
                last = message
                i += 1

        print(f"{i} messages processed.", flush=True)
        await ctx.send(f"Done. Last message: {last.jump_url}")


def setup(bot: CustomClient):
    bot.add_cog(CountEmojiCog(bot))
