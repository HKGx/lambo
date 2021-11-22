from datetime import date, datetime
from discord.ext.commands import Cog, command, Context, is_owner
import discord

from lambo.custom_client import CustomClient
from lambo.models.used_emoji_model import UsedEmojiModel
from lambo.utils import DateConverter

from typing import AsyncIterable, Iterator


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


class CountEmojiCog(Cog):
    bot: CustomClient

    def __init__(self, bot: CustomClient):
        self.bot = bot
        print("Loaded count emoji cog.")

    @ Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:  # type: ignore
            return
        if message.guild is None:  # type: ignore
            return
        if message.content.startswith(self.bot.command_prefix):  # type: ignore
            return
        parse = parse_message(message)
        await UsedEmojiModel.bulk_create(parse)

    @ command(name="emojis")
    async def emojis(self, ctx: Context, emoji: discord.Emoji, from_date: DateConverter = None, to_date: DateConverter = None):
        if emoji.guild is None:
            await ctx.send("This emoji is not in a guild.")
            return
        from_: datetime = datetime.combine(
            from_date, datetime.min.time()) if from_date is not None else datetime.min  # type: ignore
        to_: datetime = datetime.combine(
            to_date, datetime.max.time()) if to_date is not None else datetime.now()  # type: ignore
        emojis_count = await UsedEmojiModel.filter(
            emoji=emoji.name, timestamp__gte=from_, timestamp__lte=to_).count()
        from_str = from_.strftime("%d.%m.%Y")
        to_str = to_.strftime("%d.%m.%Y")
        await ctx.send(f"{emoji} was used {emojis_count} times from {from_str} to {to_str}.")

    @is_owner()
    @ command(name="load-history")
    async def load_history(self, ctx: Context, limit: int, before: discord.Message = None):
        if before is None:
            before = ctx.message  # type: ignore
        limit = min(limit, 10000)
        await ctx.send("Loading history...")
        i = 0
        last = before
        async with ctx.typing():
            channel: discord.TextChannel = ctx.channel   # type: ignore
            async for message in channel.history(limit=limit, before=before):
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
