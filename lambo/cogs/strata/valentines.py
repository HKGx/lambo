import asyncio

import discord
from discord.ext.commands import BucketType, Cog, Context, command, cooldown
from lambo import CustomClient


class ValentinesCog(Cog, name="Valentines"):

    VALENTINES_CHANNEL_ID = 941365482731216936
    SPAM_CHANNEL_ID = 412151174641221632
    EMBED_PINK = discord.Colour(0xF7A9E9)

    @property
    def valentines_channel(self) -> discord.TextChannel:
        channel = self.bot.get_channel(self.VALENTINES_CHANNEL_ID)
        if not channel:
            raise RuntimeError(
                f"Could not find channel with id {self.VALENTINES_CHANNEL_ID}"
            )
        if not channel.type == discord.ChannelType.text:  # type: ignore
            raise RuntimeError(
                f"Channel with id {self.VALENTINES_CHANNEL_ID} is not a text channel"
            )
        return channel  # type: ignore

    @property
    def spam_channel(self) -> discord.TextChannel:
        channel = self.bot.get_channel(self.SPAM_CHANNEL_ID)
        if not channel:
            raise RuntimeError(f"Could not find channel with id {self.SPAM_CHANNEL_ID}")
        if not channel.type == discord.ChannelType.text:  # type: ignore
            raise RuntimeError(
                f"Channel with id {self.VALENTINES_CHANNEL_ID} is not a text channel"
            )
        return channel  # type: ignore

    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @cooldown(1, 60, BucketType.user)
    @command(
        "ship",
    )
    async def ship(
        self, ctx: Context, first_member: discord.Member, second_member: discord.Member
    ):
        """
        Ship two members together.
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        footer_split = "—" * 23
        message_builder = [
            "** **",  # necessary to prevent the embed from being too narrow
            f"{first_member.mention} x {second_member.mention}",
            "",
            footer_split,
            f"Możesz wysłać swoją propozycję shipu komendą `*ship` na kanale {self.spam_channel.mention}",
        ]
        message = "\n".join(message_builder)
        embed = discord.Embed(
            colour=self.EMBED_PINK, title="PROPOZYCJA SHIPU:", description=message
        )
        msg = await self.valentines_channel.send(embed=embed)
        await asyncio.gather(*[msg.add_reaction(emoji) for emoji in ["❤️", "💔"]])


def setup(bot: CustomClient):
    bot.add_cog(ValentinesCog(bot))
