import asyncio

from datetime import datetime, timedelta

import discord
from discord.ext.commands import Cog, Context, command
from discord.utils import escape_markdown, format_dt
from lambo import CustomClient
from lambo.utils import get_guild, get_role
from lambo.utils.caches import TTLCache


class RolePingBlockCog(Cog, name="Role Ping Blocking"):
    LOOKUP_GUILD_ID = 211261411119202305
    BLOCKED_ROLE_ID = 953718724614037525
    ALLOWED_GUILD_IDS = [211261411119202305]
    DISABLE_ROLE_COOLDOWN = timedelta(minutes=10)
    TIMEOUT_TIME = timedelta(hours=8)
    PING_COOLDOWN = timedelta(minutes=30)

    @property
    def lookup_guild(self) -> discord.Guild:
        return get_guild(self.bot, self.LOOKUP_GUILD_ID)

    @property
    def blocked_role(self) -> discord.Role:
        return get_role(self.lookup_guild, self.BLOCKED_ROLE_ID)

    bot: CustomClient
    cache: TTLCache[int, None]

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot
        self.cache = TTLCache(expiration_time=self.PING_COOLDOWN)

    @Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.guild is not None and message.guild.id not in self.ALLOWED_GUILD_IDS:
            return

        if message.author.bot:
            return

        if self.blocked_role not in message.role_mentions:
            return

        if message.author.id in self.cache:
            if isinstance(message.author, discord.Member):
                try:
                    await message.author.timeout_for(
                        self.TIMEOUT_TIME, reason="Role ping block"
                    )
                    await message.channel.send(
                        f"Hej {message.author.mention}, otrzymałeś wyciszenie na 8 godzin"
                        ", ponieważ spingowałeś rolę 2 razy w ciągu 30 ostatnich minut. "
                        "Jest to zabezpieczenie, które ma chronić serwer przed masowym "
                        "pingowaniem roli. Spokojnie, Twoje wyciszenie nie będzie "
                        "liczyło się do historii mutów i niedługo ktoś z Support Teamu "
                        "sprawdzi czy twój podwójny ping był przez przypadek, czy też był celowy."
                    )
                except discord.Forbidden:
                    await message.channel.send("Nie mogłem nadać wyciszenia.")

                return
        self.cache[message.author.id] = None
        dt = format_dt(datetime.now() + self.PING_COOLDOWN)
        total_minutes = self.PING_COOLDOWN.total_seconds() // 60
        await message.channel.send(
            f"Pamiętaj, że możesz pingować rolę raz na {total_minutes} minut.\n"
            f"Następny ping możesz wykonać za {dt}, inaczej dostaniesz wyciszenie."
        )
        await self.blocked_role.edit(mentionable=False)
        await asyncio.sleep(self.DISABLE_ROLE_COOLDOWN.total_seconds())
        await self.blocked_role.edit(mentionable=True)

    @command(name="cooldown")
    async def get_cooldown(self, ctx: Context):
        if ctx.guild is None or ctx.guild.id not in self.ALLOWED_GUILD_IDS:
            return
        if ctx.author.id in self.cache:
            expiration = self.cache.get_expiration(ctx.author.id)
            dt = format_dt(expiration)
            await ctx.reply(f"Twój cooldown kończy się o {dt}")
        else:
            await ctx.reply("Nie masz cooldownu.")


def setup(bot: CustomClient):
    bot.add_cog(RolePingBlockCog(bot))
