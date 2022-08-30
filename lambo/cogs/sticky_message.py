import typing

import discord
from discord.ext.commands import Cog, Context, command, group, is_owner
from discord.utils import escape_markdown

from lambo.main import CustomClient
from lambo.models import StickyMessageModel


class StickyMessageCog(Cog, name="Sticky Message"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @is_owner()
    @group(name="sticky", invoke_without_command=False)
    async def sticky(self, ctx: Context):
        pass

    @sticky.command("set")
    async def sticky_set_message(
        self,
        ctx: Context,
        channel: discord.TextChannel,
        *,
        message_content: str,
    ):
        new_message = await channel.send(message_content)
        msg, created = await StickyMessageModel.get_or_create(
            channel_id=channel.id,
            defaults={
                "bot_last_message_id": new_message.id,
                "message_content": message_content,
            },
        )
        msg.message_content = message_content
        try:
            last_message = await channel.fetch_message(int(msg.bot_last_message_id))
            await last_message.delete()
        except discord.NotFound:
            pass
        msg.bot_last_message_id = str(new_message.id)
        return await msg.save(update_fields=("bot_last_message_id",))

    @sticky.command("remove")
    async def sticky_remove_message(self, ctx: Context, channel: discord.TextChannel):
        sticky_message = await StickyMessageModel.get_or_none(channel_id=channel.id)
        if sticky_message is None:
            return
        await sticky_message.delete()
        try:
            message = await channel.fetch_message(
                int(sticky_message.bot_last_message_id)
            )
            await message.delete()
        except discord.NotFound:
            pass

    @Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        msg = await StickyMessageModel.get_or_none(channel_id=message.channel.id)
        if not msg:
            return

        new_message = await message.channel.send(msg.message_content)
        try:
            last_message = await message.channel.fetch_message(
                int(msg.bot_last_message_id)
            )
            await last_message.delete()
        except discord.NotFound:
            pass
        msg.bot_last_message_id = str(new_message.id)
        return await msg.save(update_fields=("bot_last_message_id",))


async def setup(bot: CustomClient):
    await bot.add_cog(StickyMessageCog(bot))
