import asyncio
from email import message
from logging import exception
from typing import Any, Coroutine, Union
import discord
from .StrataCog import StrataCog
from discord.ext.commands import Cog, Context, group, check, command
from lambo import CustomClient


class ReminderCog(StrataCog, name="Reminder"):
    @command(name="remind", aliases=("remindme", "reminder"))
    @check(StrataCog.caretakers_only)
    async def remind(
        self,
        ctx: Context,
        emoji: discord.PartialEmoji | str,
        partial_message: discord.PartialMessage,
        *,
        content: str,
    ):
        message = await partial_message.fetch()  # refetch the message
        reaction = next(
            (reaction for reaction in message.reactions if reaction.emoji == emoji),
            None,
        )
        if reaction is None:
            await ctx.send("Nie znaleziono reakcji na wiadomość.")
            return
        content_to_send = (
            f"__**{ctx.author.mention} wysyła ci powiadomienie:**__\n\n{content}"
        )
        async with ctx.typing():
            tasks: list[Coroutine[Any, Any, discord.Message]] = []
            users = await reaction.users().flatten()
            for user in users:
                if user.bot:
                    continue
                tasks.append(user.send(content_to_send))
            gathered: list[Union[discord.Message, Exception]] = await asyncio.gather(
                *tasks, return_exceptions=True
            )

        users_with_errors = [
            user
            for user, result in zip(users, gathered)
            if isinstance(result, Exception)
        ]
        users_list = ", ".join(f"{user} ({user.id})" for user in users_with_errors)
        await ctx.reply(
            f"Udało się wysłać {len(gathered) - len(users_with_errors)}/{len(gathered)} wiadomości.\n"
            "Wiadomość nie dotarła do:\n" + users_list
        )


def setup(bot: CustomClient):
    bot.add_cog(ReminderCog(bot))
