from datetime import datetime

import discord
from discord.ext.commands import Cog, Context, group, is_owner
from discord.utils import DISCORD_EPOCH
from lambo.custom_client import CustomClient
from lambo.models.used_emoji_model import UsedEmojiModel
from lambo.utils import DateConverter
from tortoise.functions import Count

_EPOCH = datetime.utcfromtimestamp(DISCORD_EPOCH / 1000)


def get_guild_emojis_from_str(string: str, guild: discord.Guild) -> set[str]:
    emojis = set()
    for emoji in guild.emojis:
        if str(emoji) in string:
            emojis.add(emoji.name)
    return emojis


def parse_message(message: discord.Message) -> list[UsedEmojiModel]:
    emojis = get_guild_emojis_from_str(
        message.content, message.guild)  # type: ignore
    author_id: int = message.author.id  # type: ignore
    return [UsedEmojiModel(emoji=emoji, used_by=str(author_id), timestamp=message.created_at) for emoji in emojis]


def get_timestamp_tag(timestamp: datetime) -> str:
    if timestamp < _EPOCH:
        timestamp = _EPOCH
    from_unix = int(datetime.timestamp(timestamp))
    return f"<t:{from_unix}>"


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
        parse = parse_message(message)
        await UsedEmojiModel.bulk_create(parse)

    @group(name="emojis")
    async def emojis(self, ctx: Context):
        pass

    @emojis.command(name="count", aliases=("c",))
    async def emojis_count(self, ctx: Context, emoji: discord.Emoji, from_date: DateConverter = None, to_date: DateConverter = None):
        if emoji.guild is None:
            await ctx.send("This emoji is not in a guild.")
            return
        from_: datetime = datetime.combine(
            from_date, datetime.min.time()) if from_date is not None else _EPOCH  # type: ignore
        to_: datetime = datetime.combine(
            to_date, datetime.max.time()) if to_date is not None else datetime.now()  # type: ignore
        emojis_count = await UsedEmojiModel.filter(
            emoji=emoji.name, timestamp__gte=from_, timestamp__lte=to_).count()
        from_str = get_timestamp_tag(from_)
        to_str = get_timestamp_tag(to_)
        await ctx.send(f"{emoji} was used {emojis_count} times from {from_str} to {to_str}.")

    @emojis.command(name="users", aliases=("u",))
    async def emojis_users(self, ctx: Context, emoji: discord.Emoji, from_date: DateConverter = None, to_date: DateConverter = None):
        if emoji.guild is None:
            await ctx.send("This emoji is not in a guild.")
            return
        from_: datetime = datetime.combine(
            from_date, datetime.min.time()) if from_date is not None else _EPOCH  # type: ignore
        to_: datetime = datetime.combine(
            to_date, datetime.max.time()) if to_date is not None else datetime.now()  # type: ignore
        # Get all users who used the emoji and their count
        users: list[dict[str, int]] = (
            await UsedEmojiModel
            .annotate(count=Count("used_by"))
            .group_by("used_by")
            .order_by("-count")
            .filter(
                emoji=emoji.name,
                timestamp__gte=from_,
                timestamp__lte=to_
            ).limit(10)
            .values("used_by", "count")  # type: ignore
        )
        # All usages during the time period
        emojis_count = await UsedEmojiModel.filter(
            emoji=emoji.name, timestamp__gte=from_, timestamp__lte=to_).count()
        from_str = get_timestamp_tag(from_)
        to_str = get_timestamp_tag(to_)

        sb = f"{emoji} user usages from {from_str} to {to_str}."
        for user in users:
            percentage = round(user["count"] / emojis_count * 100, 2)
            sb += f"\n<@{user['used_by']}> used {user['count']} times ({percentage}%)."
        await ctx.send(sb, allowed_mentions=discord.AllowedMentions(users=False))

    @emojis.command(name="rank", aliases=("r", "ranking"))
    async def emojis_rank(self, ctx: Context, from_date: DateConverter = None, to_date: DateConverter = None):
        from_: datetime = datetime.combine(
            from_date, datetime.min.time()) if from_date is not None else _EPOCH  # type: ignore
        to_: datetime = datetime.combine(
            to_date, datetime.max.time()) if to_date is not None else datetime.now()  # type: ignore

        values: list[dict[str, int | str]] = (await UsedEmojiModel.annotate(count=Count("id"))      # type: ignore
                                              .filter(timestamp__gte=from_, timestamp__lte=to_)
                                              .limit(10)
                                              .group_by("emoji")
                                              .order_by("-count")
                                              .values("emoji", "count"))

        from_str = get_timestamp_tag(from_)
        to_str = get_timestamp_tag(to_)
        content = f"Ranking from {from_str} to {to_str}\n"
        assert isinstance(ctx.guild, discord.Guild)
        for g in values:
            guild_emojis: tuple[discord.Emoji, ...] = ctx.guild.emojis
            emoji: discord.Emoji = [
                e for e in guild_emojis if e.name == g["emoji"]][0]  # type: ignore
            content += f"{emoji} was used {g['count']} times.\n"
        await ctx.send(content)

    @is_owner()
    @emojis.command(name="load-history", hidden=True)
    async def load_history(self, ctx: Context, limit: int, before: discord.Message = None):
        before_message: discord.Message = before if before is not None else ctx.message  # type: ignore
        limit = min(limit, 10000)
        await ctx.send("Loading history...")
        i = 0
        last = before_message
        async with ctx.typing():
            channel: discord.TextChannel = ctx.channel   # type: ignore
            async for message in channel.history(limit=limit, before=before_message):
                if message.author.bot:  # type: ignore
                    continue
                if message.content.startswith(self.bot.command_prefix):
                    continue
                parse = parse_message(message)
                last = message
                await UsedEmojiModel.bulk_create(parse)
                i += 1
                if i % 10 == 0:
                    print(f"{i} messages processed.")

        print(f"{i} messages processed.", flush=True)
        await ctx.send(f"Done. Last message: {last.jump_url}")


def setup(bot: CustomClient):
    bot.add_cog(CountEmojiCog(bot))
