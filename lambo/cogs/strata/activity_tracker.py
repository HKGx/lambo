import asyncio
from datetime import date, timedelta
from typing import Optional

import discord
from discord.ext.commands import Cog, Context, command
from lambo import CustomClient
from lambo.cogs.giveaway import GiveawayCog
from lambo.models.activity_tracker_model import StageModel
from lambo.models.strata_models import ActivityTrackerModel
from lambo.utils.utils import TimedeltaConverter


class ActivityTracker(Cog, name="Activity Tracker"):
    ALLOWED_GUILD_IDS = [211261411119202305, 950868480041824266]
    ALLOWED_CHANNELS = [
        412146574823784468,  # rozmowy⭐
        533671424896925737,  # pogaduchy
        683025889658929231,  # rozmowy_dla_nowych⭐
        951215423741907005,  # baranek_test
    ]
    MODERATOR_ROLE_IDS = [303943612784181248, 950873817193000991]

    bot: CustomClient

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    async def handle_stage(
        self, stage: StageModel, channel: discord.TextChannel
    ) -> None:
        if stage.is_basic_stage():
            await channel.send(stage.response_message)
        elif stage.is_giveaway_stage():
            _, msg = await GiveawayCog.create_giveaway(
                stage.giveaway_time, stage.winners, stage.response_message, channel
            )
            await msg.pin()

    @Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.guild.id not in self.ALLOWED_GUILD_IDS:
            return
        if message.channel.id not in self.ALLOWED_CHANNELS:
            return
        if message.author.bot:
            return
        assert isinstance(message.channel, discord.TextChannel)
        today = date.today()
        model, created = await ActivityTrackerModel.get_or_create(
            channel_id=message.channel.id, date=today
        )
        if created:
            default_stages = await StageModel.filter(default=True)
            await model.stages.add(*default_stages)

        model.messages_sent += 1  # type: ignore
        stages = await model.stages.filter(messages_needed=model.messages_sent)
        await asyncio.gather(
            *[self.handle_stage(stage, message.channel) for stage in stages]
        )
        await model.save(update_fields=("messages_sent",))
        # get stages for current message count

    @command(name="list_stages")
    async def get_stages(self, ctx: Context) -> None:
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        stages = await StageModel.all().limit(10)
        stage_text = []
        for stage in stages:
            if stage.is_giveaway_stage():
                stage_text.append(
                    f"{stage.idx}::{stage.messages_needed} {stage.response_message} {stage.winners} winners (giveaway){' DEFAULT' if stage.default else ''}"
                )
            else:
                stage_text.append(
                    f"{stage.idx}::{stage.messages_needed} {stage.response_message}{' DEFAULT' if stage.default else ''}"
                )
        await ctx.send("\n".join(stage_text))

    @command(name="add_stage")
    async def add_stage(
        self, ctx: Context, messages_needed: int, *, response_message: str
    ) -> None:
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        stage = StageModel.basic_stage(
            messages_needed=messages_needed,
            response_message=response_message,
        )
        await stage.save()
        await ctx.send(
            f"Added stage {stage.idx} :: {messages_needed} :: {response_message}"
        )

    @command(name="add_gstage")
    async def add_giveaway_stage(
        self,
        ctx: Context,
        time_: TimedeltaConverter,
        messages_needed: int,
        winners: int,
        *,
        prize: str,
    ) -> None:
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        time: timedelta = time_  # type: ignore
        stage = StageModel.giveaway_stage(messages_needed, prize, winners, time)
        await stage.save()
        await ctx.send(
            f"Added giveaway stage  {stage.idx} :: {messages_needed} :: {prize} for {winners} winners"
        )

    @command(name="default_stage")
    async def set_default_stage(
        self, ctx: Context, idx: int, default: bool = True
    ) -> None:
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        await StageModel.filter(idx=idx).update(default=default)
        await ctx.send(f"Added default stage :: {idx}")

    @command(name="stage_enable")
    async def set_stage_enabled(
        self,
        ctx: Context,
        stage_index: int,
        channel: Optional[discord.TextChannel] = None,
        enable: bool = True,
    ) -> None:
        if channel is None:
            channel = ctx.channel  # type: ignore
        assert channel is not None
        if channel.guild.id not in self.ALLOWED_GUILD_IDS:
            return
        if channel.id not in self.ALLOWED_CHANNELS:
            return
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        # copy paste
        today = date.today()
        model, created = await ActivityTrackerModel.get_or_create(
            channel_id=channel.id, date=today
        )
        if created:
            default_stages = await StageModel.filter(default=True)
            await model.stages.add(*default_stages)

        stage = await StageModel.get(idx=stage_index)

        if enable:
            await model.stages.add(stage)
        else:
            await model.stages.remove(stage)

        await ctx.reply(
            f"Stage {stage_index} is now {'enabled' if enable else 'disabled'} for channel {channel}"
        )

    @command(name="messages_in")
    async def get_messages_in(
        self, ctx: Context, channel: Optional[discord.TextChannel] = None
    ):
        if channel is None:
            channel = ctx.channel  # type: ignore
        assert channel is not None
        if channel.guild.id not in self.ALLOWED_GUILD_IDS:
            return
        if channel.id not in self.ALLOWED_CHANNELS:
            return
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        today = date.today()
        today = date.today()
        model, created = await ActivityTrackerModel.get_or_create(
            channel_id=channel.id, date=today
        )
        if created:
            default_stages = await StageModel.filter(default=True)
            await model.stages.add(*default_stages)
        await ctx.reply(f"{model.messages_sent} messages sent in {channel}")

    @command("remove_stage")
    async def remove_stage(self, ctx: Context, idx: int):
        role = [role for role in ctx.author.roles if role.id in self.MODERATOR_ROLE_IDS]
        if not role:
            return
        model = await StageModel.get(idx=idx)
        await model.delete()


def setup(bot: CustomClient):
    bot.add_cog(ActivityTracker(bot))
