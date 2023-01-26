import discord
from discord.ext.commands import Cog, Context

from lambo import CustomClient
from lambo.utils import is_member


class StrataCog(Cog):
    bot: CustomClient

    ALLOWED_GUILD_IDS = [211261411119202305, 950868480041824266]
    MODERATOR_ROLE_IDS = [303943612784181248, 950873817193000991]
    CARETAKER_ROLES = [
        *MODERATOR_ROLE_IDS,
        422408722107596811,
        412193755286732800,
        303943612784181248,
    ]

    def __init__(self, bot: CustomClient) -> None:
        super().__init__()
        self.bot = bot

    def cog_check(self, ctx: Context) -> bool:
        if ctx.guild is None:
            return False
        if ctx.guild.id not in self.ALLOWED_GUILD_IDS:
            return False
        return True

    @staticmethod
    async def mod_only(ctx: Context) -> bool:
        if ctx.guild is None:
            return False
        assert is_member(ctx.author)
        assert isinstance(ctx.bot, discord.Bot)
        if await ctx.bot.is_owner(ctx.author):  # type: ignore
            return True
        return any(role.id in StrataCog.MODERATOR_ROLE_IDS for role in ctx.author.roles)

    @staticmethod
    async def caretakers_only(ctx: Context) -> bool:
        if ctx.guild is None:
            return False
        assert is_member(ctx.author)
        assert isinstance(ctx.bot, discord.Bot)
        if await ctx.bot.is_owner(ctx.author):  # type: ignore
            return True
        return any(role.id in StrataCog.CARETAKER_ROLES for role in ctx.author.roles)
