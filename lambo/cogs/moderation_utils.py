import discord
from discord.ext.commands import Cog, Context, group, has_permissions
from lambo.custom_client import CustomClient


class ModerationUtilsCog(Cog, name="Moderation Utilities"):
    bot: CustomClient

    def __init__(self, bot: CustomClient):
        self.bot = bot

    @group(name="role", invoke_without_command=False)
    @has_permissions(manage_roles=True)
    async def role(self, ctx: Context):
        pass

    @role.command(name="create")
    async def role_create(self, ctx: Context, name: str, after: discord.Role = None):
        guild: discord.Guild = ctx.guild  # type: ignore
        if after is None:
            after = guild.default_role
        assert after is not None, "after is None"
        await ctx.send(f"Creating role {name} after {after.name}")
        role: discord.Role = await guild.create_role(name=name)
        async with ctx.typing():
            await role.edit(position=after.position)
            await ctx.reply(f"Created role {role.name} with id {role.id}")

    @role.command(name="move")
    async def move_role(self, ctx: Context, role: discord.Role, after: discord.Role):
        await ctx.send(f"Moving role {role.name} after {after.name}")
        async with ctx.typing():
            await role.edit(position=after.position)
            await ctx.reply(f"Moved role {role.name} with id {role.id}")


def setup(bot: CustomClient):
    bot.add_cog(ModerationUtilsCog(bot))
