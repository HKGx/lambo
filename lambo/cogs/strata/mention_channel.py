import re

import discord
from discord.ext.commands import Cog

from lambo.main import CustomClient
from lambo.utils import get_guild


class MentionChannelCog(Cog, name="Channel Mentioning"):
    MENTION_REGEX = re.compile(r"#(\w+)")
    LOOKUP_GUILD_ID = 211261411119202305
    ALLOWED_GUILD_IDS = [950868480041824266]

    @property
    def lookup_guild(self) -> discord.Guild:
        return get_guild(self.bot, self.LOOKUP_GUILD_ID)

    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.guild is not None and message.guild.id not in self.ALLOWED_GUILD_IDS:
            return
        partial_names = self.MENTION_REGEX.findall(message.content)
        if not partial_names:
            return
        channel_mentions: list[str] = []
        for partial_name in partial_names:
            channel_mentions += [
                channel.mention
                for channel in reversed(
                    self.lookup_guild.channels
                )  # reverse to get channel with highest position
                if partial_name in channel.name
            ][
                :3
            ]  # limit to 3 channels
        if not channel_mentions:
            return
        await message.reply(
            " ".join(channel_mentions), allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot: CustomClient):
    await bot.add_cog(MentionChannelCog(bot))
