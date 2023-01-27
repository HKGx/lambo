from typing import TypeGuard
from lambo import CustomClient
from lambo.cogs.strata.strata_cog import StrataCog
import discord
from re import match


def only_strings_list(value: list) -> TypeGuard[list[str]]:
    return all(isinstance(item, str) for item in value)


class CharityStreamCog(StrataCog):
    ORGANISER_ID = 215838737102405632
    BRUNO_ID = 892004193999663104

    @property
    def organiser(self) -> discord.Member:
        if organiser := self.strata_czasu.get_member(self.ORGANISER_ID):
            return organiser
        raise ValueError("Organiser not found")

    MESSAGE_REGEX = r"<@!?(\d+)>, pomyślnie przekazano użytkownikowi <@!?(\d+)> punkty w ilości \*\*(\d+)\*\*."

    @StrataCog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        if message.author.id != self.BRUNO_ID:
            return
        if len(message.embeds) != 1:
            return
        if message.embeds[0].title != "Punkty-przekaz":
            return
        if not isinstance(message.embeds[0].description, str):
            return
        values = match(self.MESSAGE_REGEX, message.embeds[0].description)
        if not values:
            return
        sender, receiver, amount = values.groups("")
        if int(receiver) != message.guild.me.id:
            return
        sender_member = message.guild.get_member(int(sender))
        assert sender_member is not None
        mention = f"<@{sender}> ({sender_member})" if sender_member else f"<@sender>"
        await self.organiser.send(f"Użytkownik {mention} przekazał {amount} punktów.")
        await message.channel.send(
            f"Dzięki <@{sender}> 💓",
            allowed_mentions=discord.AllowedMentions(users=[sender_member]),
        )


def setup(bot: CustomClient):
    bot.add_cog(CharityStreamCog(bot))
