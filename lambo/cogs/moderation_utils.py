import typing

import discord
from discord.ext.commands import Cog, Context, FlagConverter, group, has_permissions
from lambo import CustomClient
from lambo.utils import FuzzyRoleConverter


class PermissionsFor(FlagConverter):
    read_messages: typing.Optional[bool] = None
    send_messages: typing.Optional[bool] = None


class ModerationUtilsCog(Cog, name="Moderation Utilities"):
    bot: CustomClient

    def __init__(self, bot: CustomClient):
        self.bot = bot

    @group(name="role", invoke_without_command=False)
    async def role(self, ctx: Context):
        pass

    @role.command(name="overlap")
    async def role_overlap(
        self,
        ctx: Context,
        first_role_: FuzzyRoleConverter,
        second_role_: FuzzyRoleConverter,
    ):
        first_role: discord.Role = first_role_  # type: ignore
        second_role: discord.Role = second_role_  # type: ignore
        members_overlap = set(first_role.members) & set(second_role.members)
        await ctx.reply(f"There are {len(members_overlap)} members in both roles.")

    @role.command(name="id")
    async def role_id(self, ctx: Context, _role: FuzzyRoleConverter):
        role: discord.Role = _role  # type: ignore
        await ctx.reply(f"The ID of the role {role.name} is {role.id}")

    @role.command(name="create")
    @has_permissions(manage_roles=True)
    async def role_create(self, ctx: Context, name: str, after: discord.Role = None):
        if after is None:
            after = ctx.guild.default_role
        assert after is not None, "after is None"
        await ctx.send(f"Creating role {name} after {after.name}")
        role: discord.Role = await ctx.guild.create_role(name=name)
        async with ctx.typing():
            await role.edit(position=after.position)
            await ctx.reply(f"Created role {role.name} with id {role.id}")

    @role.command(name="move")
    @has_permissions(manage_roles=True)
    async def move_role(self, ctx: Context, role: discord.Role, after: discord.Role):
        await ctx.send(f"Moving role {role.name} after {after.name}")
        async with ctx.typing():
            await role.edit(position=after.position)
            await ctx.reply(f"Moved role {role.name} with id {role.id}")

    @group(name="channel", aliaess=["ch"], invoke_without_command=False)
    async def channel(self, ctx: Context):
        pass

    @channel.group(name="permissions", aliases=["perms"], invoke_without_command=False)
    async def channel_permissions(self, ctx: Context):
        pass

    def set_channel_overwrites(
        self, overwrites: discord.PermissionOverwrite, permissions: PermissionsFor
    ) -> discord.PermissionOverwrite:
        """
        SIDE EFFECTS!
        """
        for perm, value in permissions:
            if value:
                overwrites._set(perm, value)
        return overwrites

    def check_bot_perms_for_channel(
        self,
        ctx: Context,
        channel: discord.abc.GuildChannel,
        permission: discord.flags.flag_value,
    ) -> bool:
        perm = discord.Permissions(permission.flag)
        return channel.permissions_for(ctx.guild.me) >= perm

    @channel_permissions.command(name="addfor")
    async def channel_permissions_add(
        self,
        ctx: Context,
        channel: typing.Union[
            discord.TextChannel,
            discord.CategoryChannel,
            discord.VoiceChannel,
            discord.StageChannel,
        ],
        member: discord.Member,
        *,
        permissions: PermissionsFor,
    ):
        assert isinstance(
            ctx.author, discord.Member
        ), "ctx.author is not a discord.Member"
        if not channel.permissions_for(ctx.author).manage_permissions:
            await ctx.send(
                "You do not have permission to manage permissions for this channel."
            )
            return
        await ctx.send(
            f"Adding permissions for {member.name} in {channel}. It might take a while..."
        )
        ctx.typing()
        permissions_set_for: set[str] = set()
        permissions_lacking_for: set[str] = set()
        if not self.check_bot_perms_for_channel(
            ctx, channel, discord.Permissions.manage_permissions
        ):
            permissions_lacking_for.add(channel.mention)
        else:
            overwrites: discord.PermissionOverwrite = channel.overwrites_for(
                member  # type: ignore
            )
            self.set_channel_overwrites(overwrites, permissions)
            try:
                await channel.set_permissions(member, overwrite=overwrites)
                permissions_set_for.add(channel.mention)
            except Exception as e:
                await ctx.send(
                    f"Failed to set permissions for {member.name} in {channel} : {e}"
                )
                permissions_lacking_for.add(channel.mention)
        if isinstance(channel, discord.CategoryChannel):
            for subchannel in channel.channels:
                if not self.check_bot_perms_for_channel(
                    ctx, channel, discord.Permissions.manage_permissions
                ):
                    permissions_lacking_for.add(subchannel.mention)
                    continue
                overwrites = subchannel.overwrites_for(member)  # type: ignore
                self.set_channel_overwrites(overwrites, permissions)
                try:
                    await subchannel.set_permissions(member, overwrite=overwrites)
                    permissions_set_for.add(subchannel.mention)
                except Exception as e:
                    await ctx.send(
                        f"Failed to set permissions for {member.name} in {subchannel.name} : {e}"
                    )
                    permissions_lacking_for.add(subchannel.mention)

        await ctx.reply(
            f"Set permissions for {member.name} in {', '.join(permissions_set_for)}\n"
            f"Couldn't set permissions for {', '.join(permissions_lacking_for)}"
        )


def setup(bot: CustomClient):
    bot.add_cog(ModerationUtilsCog(bot))
