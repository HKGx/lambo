import discord
from discord.ext.commands import Cog, Context


class StrataCog(Cog):
    ALLOWED_GUILD_IDS = [211261411119202305, 950868480041824266]
    MODERATOR_ROLE_IDS = [303943612784181248, 950873817193000991]

    def cog_check(self, ctx: Context) -> bool:
        if ctx.guild is None:
            return False
        if ctx.guild.id not in self.ALLOWED_GUILD_IDS:
            return False
        return True

    @staticmethod
    def mod_only(ctx: Context) -> bool:
        if ctx.guild is None:
            return False
        assert isinstance(ctx.author, discord.Member)
        return any(
            role for role in ctx.author.roles if role.id in StrataCog.MODERATOR_ROLE_IDS
        )
