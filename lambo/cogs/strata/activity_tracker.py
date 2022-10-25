import asyncio
from datetime import date, timedelta
import json
from typing import Optional

import discord
from discord.ext.commands import Cog, Context, command, check
from more_itertools import stagger

from lambo import CustomClient
from lambo.cogs.giveaway import GiveawayCog
from lambo.cogs.strata import StrataCog
from lambo.models.activity_tracker_model import (
    ExportedStageDict,
    StageModel,
    is_basic_stage,
    is_giveaway_stage,
)
from lambo.models.strata_models import ActivityTrackerModel
from lambo.utils import TimedeltaConverter, is_member

from lambo.cogs.strata.StrataCog import StrataCog

from tortoise.expressions import F
from tortoise.transactions import in_transaction


class ActivityTracker(StrataCog, name="Activity Tracker"):
    ALLOWED_CHANNELS = [
        412146574823784468,  # rozmowy⭐
        533671424896925737,  # pogaduchy
        683025889658929231,  # rozmowy_dla_nowych⭐
        951215423741907005,  # baranek_test
        412151174641221632,  # spam
    ]

    async def handle_stage(
        self, stage: StageModel, channel: discord.TextChannel
    ) -> None:
        if is_basic_stage(stage):
            await channel.send(stage.response_message)
        elif is_giveaway_stage(stage):
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

        async with in_transaction():

            model, created = await ActivityTrackerModel.get_or_create(
                channel_id=message.channel.id,
                date=today,
            )

            if created:
                default_stages = await StageModel.filter(default=True)
                await model.stages.add(*default_stages)

            await ActivityTrackerModel.filter(
                channel_id=message.channel.id,
                date=today,
            ).update(messages_sent=F("messages_sent") + 1)

            stages = await model.stages.filter(messages_needed=model.messages_sent)

        await asyncio.gather(
            *[self.handle_stage(stage, message.channel) for stage in stages]
        )

    @check(StrataCog.mod_only)
    @command(name="list_stages")
    async def get_stages(self, ctx: Context) -> None:

        stages = await StageModel.all().limit(10)
        stage_text = []
        for stage in stages:
            if is_giveaway_stage(stage):
                stage_text.append(
                    f"{stage.idx}::{stage.messages_needed} {stage.response_message} {stage.winners} winners (giveaway){' DEFAULT' if stage.default else ''}"
                )
            else:
                stage_text.append(
                    f"{stage.idx}::{stage.messages_needed} {stage.response_message}{' DEFAULT' if stage.default else ''}"
                )
        await ctx.send("\n".join(stage_text))

    @check(StrataCog.mod_only)
    @command(name="add_stage")
    async def add_stage(
        self, ctx: Context, messages_needed: int, *, response_message: str
    ) -> None:
        stage = StageModel.basic_stage(
            messages_needed=messages_needed,
            response_message=response_message,
        )
        await stage.save()
        await ctx.send(
            f"Added stage {stage.idx} :: {messages_needed} :: {response_message}"
        )

    @check(StrataCog.mod_only)
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
        time: timedelta = time_  # type: ignore
        stage = StageModel.giveaway_stage(messages_needed, prize, winners, time)
        await stage.save()
        await ctx.send(
            f"Added giveaway stage  {stage.idx} :: {messages_needed} :: {prize} for {winners} winners"
        )

    @check(StrataCog.mod_only)
    @command(name="default_stage")
    async def set_default_stage(
        self, ctx: Context, idx: int, default: bool = True
    ) -> None:
        await StageModel.filter(idx=idx).update(default=default)
        await ctx.send(f"Added default stage :: {idx}")

    @check(StrataCog.mod_only)
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
        if channel.id not in self.ALLOWED_CHANNELS:
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

    @check(StrataCog.mod_only)
    @command(name="messages_in")
    async def get_messages_in(
        self, ctx: Context, channel: Optional[discord.TextChannel] = None
    ):
        if channel is None:
            channel = ctx.channel  # type: ignore
        assert channel is not None
        if channel.id not in self.ALLOWED_CHANNELS:
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

    @check(StrataCog.mod_only)
    @command(name="remove_stage")
    async def remove_stage(self, ctx: Context, idx: int):
        assert is_member(ctx.author)
        model = await StageModel.get(idx=idx)
        await model.delete()

    @check(StrataCog.mod_only)
    @command(name="export_stages")
    async def export_stages(
        self, ctx: Context, channel: discord.TextChannel | None = None
    ):
        if channel is None:
            channel = ctx.channel  # type: ignore
        assert channel is not None

        stages = await StageModel.export_stages_for(channel.id)
        dicts: list[ExportedStageDict] = [stage.as_dict() for stage in stages]
        data = json.dumps(dicts, indent=2)
        text = f"```json\n{data}\n```"
        await ctx.send(text)

    @check(StrataCog.mod_only)
    @command(name="import_stages")
    async def import_stages(
        self, ctx: Context, channel: discord.TextChannel | None = None, *, data: str
    ):
        if channel is None:
            channel = ctx.channel  # type: ignore
        assert channel is not None
        if channel.id not in self.ALLOWED_CHANNELS:
            return

        exported_stages: list[ExportedStageDict] = json.loads(data)
        stages = [StageModel.from_dict(stage) for stage in exported_stages]
        async with in_transaction():
            model = await ActivityTrackerModel.filter(
                channel_id=str(channel.id)
            ).get_or_none()
            if model is None:
                model = ActivityTrackerModel(channel_id=channel.id, date=date.today())
                await model.save()
            else:
                await model.stages.clear()
            for stage in stages:
                await stage.save()
                await model.stages.add(stage)
        await ctx.send(f"Imported {len(stages)} stages for {channel}")


def setup(bot: CustomClient):
    bot.add_cog(ActivityTracker(bot))
