import asyncio
from datetime import datetime, timedelta
from random import sample
from typing import Optional, Tuple, Union, overload

import discord
from discord.embeds import EmptyEmbed
from discord.ext.commands import Cog, Context, command
from discord.ext.tasks import loop
from discord.utils import format_dt

from lambo import CustomClient
from lambo.models import giveway_model
from lambo.models.giveway_model import GiveawayModel
from lambo.utils.utils import TimedeltaConverter, get_text_channel


class GiveawayCog(Cog, name="Template"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot
        self.check_giveaway.start()

    def cog_unload(self) -> None:
        self.check_giveaway.cancel()

    @loop(seconds=5.0)
    async def check_giveaway(self):
        ended_giveaways = await GiveawayModel.filter(
            ends_at__lt=datetime.utcnow(), ended=False
        )
        end_actions = [
            self.end_giveaway(self.bot, giveaway) for giveaway in ended_giveaways
        ]
        results = await asyncio.gather(*end_actions)
        if results:
            await GiveawayModel.bulk_update(results, ["ended"])

    @staticmethod
    def giveaway_embed(
        giveaway: GiveawayModel,
        author: Optional[Union[discord.Member, discord.User]] = None,
    ) -> discord.Embed:
        author_name = str(author) if author else EmptyEmbed
        author_icon = author.display_avatar.url if author else EmptyEmbed
        return (
            discord.Embed(title="Giveaway", color=0x00FF00)
            .set_footer(text=author_name, icon_url=author_icon)
            .add_field(name="To win", value=giveaway.prize, inline=False)
            .add_field(name="Winners", value=str(giveaway.winners), inline=False)
            .add_field(name="Ends at", value=format_dt(giveaway.ends_at), inline=False)
        )

    @overload
    @staticmethod
    async def create_giveaway(
        end_time: timedelta,
        winners: int,
        prize: str,
        message: Union[discord.Message, discord.TextChannel],
        author: Optional[Union[discord.Member, discord.User]] = None,
    ) -> Tuple[GiveawayModel, discord.Message]:
        ...

    @overload
    @staticmethod
    async def create_giveaway(
        end_time: datetime,
        winners: int,
        prize: str,
        message: Union[discord.Message, discord.TextChannel],
        author: Optional[Union[discord.Member, discord.User]] = None,
    ) -> Tuple[GiveawayModel, discord.Message]:
        ...

    @staticmethod
    async def create_giveaway(
        end_time: Union[datetime, timedelta],
        winners: int,
        prize: str,
        message: Union[discord.Message, discord.TextChannel],
        author: Optional[Union[discord.Member, discord.User]] = None,
    ) -> Tuple[GiveawayModel, discord.Message]:

        msg = await (
            message.reply(content="Giveaway, add reactions to enter")
            if isinstance(message, discord.Message)
            else message.send(content="Giveaway, add reactions to enter")
        )
        if isinstance(end_time, timedelta):
            end_time = datetime.utcnow() + end_time
        giveaway = await GiveawayModel.create(
            message_id=msg.id,
            channel_id=msg.channel.id,
            ends_at=end_time,
            prize=prize,
            winners=winners,
        )
        embed = GiveawayCog.giveaway_embed(giveaway, author)
        await msg.edit(embed=embed)
        await msg.add_reaction("🎉")
        return (giveaway, msg)

    @staticmethod
    async def get_giveaway_winners(
        message: discord.Message, giveaway: GiveawayModel
    ) -> list[discord.User | discord.Member] | None:
        reaction = [reaction for reaction in message.reactions if reaction.emoji == "🎉"]
        if not reaction:
            return None

        reacted_users = await reaction[0].users().flatten()
        reacted_members = [
            user
            for user in reacted_users
            if not user.bot and isinstance(user, discord.Member)
        ]

        winner_count = min(giveaway.winners, len(reacted_members))
        if winner_count == 0:
            return []

        return sample(reacted_members, winner_count)

    @staticmethod
    async def end_giveaway(bot: CustomClient, giveaway: GiveawayModel) -> GiveawayModel:
        giveaway.ended = True  # type: ignore
        channel_id = int(giveaway.channel_id)
        message_id = int(giveaway.message_id)
        try:
            channel = get_text_channel(bot, channel_id)
            message = await channel.fetch_message(message_id)
        except (ValueError, discord.NotFound, discord.Forbidden):
            return giveaway

        winners = await GiveawayCog.get_giveaway_winners(message, giveaway)
        if not winners:
            await message.reply(content="No one won the giveaway")
            return giveaway
        winners_mentions = ", ".join(winner.mention for winner in winners)
        await message.reply(
            f"{winners_mentions} won the giveaway!",
            allowed_mentions=discord.AllowedMentions(users=True),
        )

        await message.edit(
            embed=message.embeds[0].set_field_at(
                2, name="Winners", value=winners_mentions, inline=False
            )
        )

        return giveaway

    @command(name="giveaway", aliases=("gstart",))
    async def giveaway_cmd(
        self,
        ctx: Context,
        time_converter: TimedeltaConverter,
        winners: Optional[int] = None,
        *,
        message: str,
    ) -> None:
        if winners is None:
            winners = 1
        if winners < 1:
            raise ValueError("Winners must be at least 1")

        time: timedelta = time_converter  # type: ignore

        end_time = datetime.utcnow() + time
        author: Union[discord.Member, discord.User] = ctx.author  # type: ignore
        await self.create_giveaway(end_time, winners, message, ctx.message, author)

    @command(name="reroll")
    async def reroll_cmd(
        self, ctx: Context, message: Optional[discord.Message] = None
    ) -> None:
        if message is None:
            if ctx.message.reference is None:
                raise ValueError("No message provided")
            message_id = ctx.message.reference.message_id
        else:
            message_id = message.id
        giveaway = await GiveawayModel.get_or_none(message_id=message_id)
        if giveaway is None:
            await ctx.reply("No giveaway found for this message")
            return
        if not giveaway.ended:
            await ctx.reply("This giveaway is still running")
            return
        channel = self.bot.get_channel(int(giveaway.channel_id))
        if channel is None:
            await ctx.reply("Channel not found")
            return
        message = await channel.fetch_message(int(giveaway.message_id))  # type: ignore
        if message is None:
            await ctx.reply("Message not found")
            return
        if message.reference is None:
            await ctx.reply("Message is not a reply")
            return
        if message.reference.message_id is None:
            await ctx.reply("Message is not a reply")
            return
        original_message = await channel.fetch_message(message.reference.message_id)  # type: ignore
        if ctx.author != original_message.author:
            await ctx.reply("You are not the author of this giveaway")
            return
        await self.end_giveaway(self.bot, giveaway)

    @command(name="freroll")
    async def fake_reroll_cmd(
        self, ctx: Context, message: Optional[discord.Message] = None
    ) -> None:
        if message is None:
            if ctx.message.reference is None:
                raise ValueError("No message provided")
            message_id = ctx.message.reference.message_id
        else:
            message_id = message.id
        giveaway = await GiveawayModel.get_or_none(message_id=message_id)
        if giveaway is None:
            await ctx.reply("No giveaway found for this message")
            return
        if not giveaway.ended:
            await ctx.reply("This giveaway is still running")
            return
        channel = self.bot.get_channel(int(giveaway.channel_id))
        if channel is None:
            await ctx.reply("Channel not found")
            return
        message = await channel.fetch_message(int(giveaway.message_id))  # type: ignore
        if message is None:
            await ctx.reply("Message not found")
            return
        winners = await self.get_giveaway_winners(message, giveaway)
        if winners is None:
            await ctx.reply("No one won the giveaway")
            return
        winners_mentions = ", ".join(winner.mention for winner in winners)
        await ctx.reply(
            f"{winners_mentions} won the giveaway!",
        )


def setup(bot: CustomClient):
    bot.add_cog(GiveawayCog(bot))
