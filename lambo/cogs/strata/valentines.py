import asyncio

import discord
from discord.ext.commands import BucketType, Cog, Context, command, cooldown

from lambo import CustomClient
from lambo.utils import get_text_channel


class ValentinesCog(Cog, name="Valentines"):
    VALENTINES_CHANNEL_ID = 941365482731216936
    ANNOUNCEMENT_CHANNEL_ID = 412146574823784468
    SPAM_CHANNEL_ID = 412151174641221632
    EMBED_COLOUR = discord.Colour(0xEA4242)

    @property
    def valentines_channel(self) -> discord.TextChannel:
        return get_text_channel(self.bot, self.VALENTINES_CHANNEL_ID)

    @property
    def spam_channel(self) -> discord.TextChannel:
        return get_text_channel(self.bot, self.SPAM_CHANNEL_ID)

    @property
    def announcement_channel(self) -> discord.TextChannel:
        return get_text_channel(self.bot, self.ANNOUNCEMENT_CHANNEL_ID)

    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    async def post_announcement(self) -> None:
        message = f"Na kanale {self.valentines_channel.mention} została wysłana nowa propozycja shipu!"
        await self.announcement_channel.send(message)

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
            colour=self.EMBED_COLOUR, title="PROPOZYCJA SHIPU:", description=message
        )
        msg = await self.valentines_channel.send(embed=embed)
        actions = [
            *[msg.add_reaction(emoji) for emoji in ("❤️", "💔")],
            self.post_announcement(),
        ]
        await asyncio.gather(*actions)


def setup(bot: CustomClient):
    bot.add_cog(ValentinesCog(bot))
