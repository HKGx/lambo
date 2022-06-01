import asyncio
import typing

import discord
import tortoise.transactions
from discord.ext.commands import Cog, Context, command, group

from lambo import CustomClient
from lambo.models import StickyMessageModel, AddReactionModel


class AddReactionCog(Cog, name="Add Reaction"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @group(name="addreaction", invoke_without_command=False)
    async def add_reaction(self, ctx: Context):
        pass

    @add_reaction.command("set")
    @tortoise.transactions.atomic()
    async def add_reaction_set_reaction(
        self, ctx: Context, channel: discord.TextChannel, emoji: discord.Emoji
    ):
        if await AddReactionModel.exists(channel_id=channel.id, emoji_id=emoji.id):
            await ctx.reply("This reaction is already set.")
            return
        await AddReactionModel.create(channel_id=channel.id, emoji_id=emoji.id)

    @add_reaction.command("remove")
    @tortoise.transactions.atomic()
    async def add_reaction_remove(
        self, ctx: Context, channel: discord.TextChannel, emoji: discord.Emoji
    ):
        removed = await AddReactionModel.filter(
            channel_id=channel.id, emoji_id=emoji.id
        ).delete()
        await ctx.reply(f"Removed {removed} reactions.")

    @Cog.listener("on_message")
    @tortoise.transactions.atomic()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        emoji_model = await AddReactionModel.filter(channel_id=message.channel.id)
        if not emoji_model:
            return
        emojis = map(self.bot.get_emoji, map(lambda m: int(m.emoji_id), emoji_model))
        actions = []
        for emoji in emojis:
            if not emoji:
                continue
            actions.append(message.add_reaction(emoji))
        await asyncio.gather(*actions)


def setup(bot: CustomClient):
    bot.add_cog(AddReactionCog(bot))
