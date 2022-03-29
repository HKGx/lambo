from datetime import date, datetime
import typing

import discord
from discord import Guild, Role
from discord.ext.commands import Context, Converter, RoleConverter, RoleNotFound
from lambo.custom_client import CustomClient


class FuzzyRoleConverter(RoleConverter):
    async def convert(self, ctx: Context, argument: str) -> Role:
        try:
            role = await super().convert(ctx, argument)
            return role
        except RoleNotFound as e:
            guild: Guild = ctx.guild  # type: ignore
            if guild == None:
                raise e
            matching_roles = [
                role
                for role in guild._roles.values()
                if argument.lower() in role.name.lower()
            ]
            if len(matching_roles) == 0:
                raise e
            return matching_roles[0]


class DateConverter(Converter):
    async def convert(self, ctx: Context, argument: str) -> date:
        # Parse the date from the argument string.
        # Date is expected to be in a human readble format.
        # Example: "2020-01-01", "2020.01.01", "01.01.2020", "01-01-2020"
        try:
            return datetime.strptime(argument, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(argument, "%Y.%m.%d").date()
            except ValueError:
                try:
                    return datetime.strptime(argument, "%d.%m.%Y").date()
                except ValueError:
                    try:
                        return datetime.strptime(argument, "%d-%m-%Y").date()
                    except ValueError:
                        raise ValueError(
                            f"Date format not recognized. Please use one of the following formats: "
                            f"`yyyy-mm-dd`, `yyyy.mm.dd`, `dd.mm.yyyy`, `dd-mm-yyyy`"
                        )


def get_text_channel(bot: CustomClient, channel_id: int) -> discord.TextChannel:
    channel = bot.get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel with id {channel_id} not found.")
    if channel.type != discord.ChannelType.text:  # type: ignore
        raise ValueError(f"Channel with id {channel_id} is not a text channel.")
    return channel  # type: ignore


def get_guild(bot: CustomClient, guild_id: int) -> discord.Guild:
    guild = bot.get_guild(guild_id)
    if not guild:
        raise ValueError(f"Guild with id {guild_id} not found.")
    return guild


def get_role(guild: discord.Guild, role_id: int) -> discord.Role:
    role = guild.get_role(role_id)
    if not role:
        raise ValueError(f"Role with id {role_id} not found.")
    return role


def unwrap_channels(
    channel: discord.abc.GuildChannel,
) -> typing.List[
    typing.Union[
        discord.TextChannel,
        discord.VoiceChannel,
        discord.CategoryChannel,
        discord.StageChannel,
    ]
]:
    if isinstance(channel, discord.TextChannel):
        return [channel]
    if isinstance(channel, discord.VoiceChannel):
        return [channel]
    if isinstance(channel, discord.StageChannel):
        return [channel]
    if isinstance(channel, discord.CategoryChannel):
        return [
            unwrapped
            for child in channel.channels
            for unwrapped in unwrap_channels(child)
        ]
    raise ValueError(f"Unknown channel type: {channel}")


def quoted(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines())


def codized(text: str) -> str:
    return f"```\n{text}\n```"