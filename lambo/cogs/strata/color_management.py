import json
from math import ceil
import typing
import discord
from discord.ext.commands import Context, check, group
import tortoise.exceptions

from lambo import CustomClient
from lambo.cogs.strata.StrataCog import StrataCog
from lambo.models.color_role_model import ColorRoleModel


class ColorManagement(StrataCog, name="Color Management"):
    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @group("colors", invoke_without_command=False)
    async def colors(self, ctx: Context):
        pass

    @colors.command("hex")
    async def colors_set_hex(
        self, ctx: Context, color: discord.Color, *, role: discord.Role
    ):
        if not await self.is_color_owner(ctx.author, role):
            await ctx.reply("You're not the owner!")
        await role.edit(color=color)
        await ctx.reply("Color changed! :)")

    @check(StrataCog.mod_only)
    @colors.command("add")
    async def colors_add_role(
        self, ctx: Context, user: discord.Member, *, role: discord.Role
    ):
        try:
            _, created = await ColorRoleModel.get_or_create(
                {"owner_id": user.id, "role_id": role.id}
            )
            if created:
                await ctx.reply(f"Added color {role}")
            else:
                await ctx.reply(f"Color {role} already exists!")
        except tortoise.exceptions.IntegrityError:
            await ctx.reply(f"Color {role} already exists and has a different owner!")

    @check(StrataCog.mod_only)
    @colors.command("remove")
    async def colors_remove_role(self, ctx: Context, *, role: discord.Role):
        removed = await ColorRoleModel.filter(role_id=role.id).delete()
        await ctx.reply(f"Removed {removed} color :)")

    @check(StrataCog.mod_only)
    @colors.command("import")
    async def colors_import(self, ctx: Context, *, value: str):
        content = value
        if len(ctx.message.attachments) > 0:
            content = str(await ctx.message.attachments[0].read())

        roles_raw = json.loads(content)
        models: list[ColorRoleModel] = []
        assert ctx.guild is not None
        for role_name, owner_id in roles_raw:
            assert isinstance(owner_id, str)
            assert isinstance(role_name, str)
            possible_roles = [
                role.id for role in ctx.guild.roles if role.name == role_name
            ]
            if len(possible_roles) == 0:
                print(role_name)
                continue
            role_id = possible_roles[0]
            models.append(ColorRoleModel(owner_id=owner_id, role_id=role_id))
        try:
            imported = await ColorRoleModel.bulk_create(models, ignore_conflicts=True)
            await ctx.reply(f"Imported {imported} roles")
        except:
            await ctx.reply("Something went wrong. Try binary deduction :)")

    @colors.command("list")
    async def colors_list(self, ctx: Context, page: int = 1):
        assert ctx.guild is not None
        count = await ColorRoleModel.all().count()
        models = await ColorRoleModel.all().limit(20).offset(20 * (page - 1))
        strbuilder = [f"page {page} of circa {ceil(count / 20)}"]
        for model in models:
            role = ctx.guild.get_role(int(model.role_id))
            owner = ctx.guild.get_member(int(model.owner_id))
            strbuilder.append(f"{role}: {owner}")
        await ctx.reply("\n".join(strbuilder))

    async def is_color_owner(
        self, user: typing.Union[discord.Member, discord.User], role: discord.Role
    ) -> bool:
        color = await ColorRoleModel.get_or_none(owner_id=user.id, role_id=role.id)
        return color is not None


def setup(bot: CustomClient):
    bot.add_cog(ColorManagement(bot))
