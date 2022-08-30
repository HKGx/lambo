import asyncio
import json
from datetime import date, timedelta
from io import BytesIO
from typing import BinaryIO, Optional, TextIO

import discord
from discord.ext.commands import Cog, Context, check, command, group

from lambo.cogs.giveaway import GiveawayCog
from lambo.cogs.strata.StrataCog import StrataCog
from lambo.main import CustomClient
from lambo.models.activity_tracker_model import StageModel
from lambo.models.strata_models import ActivityTrackerModel
from lambo.utils.utils import TimedeltaConverter


class ActivityTracker(StrataCog, name="Activity Tracker"):
    ALLOWED_CHANNELS = [
        412146574823784468,  # rozmowy⭐
        533671424896925737,  # pogaduchy
        683025889658929231,  # rozmowy_dla_nowych⭐
        951215423741907005,  # baranek_test
    ]
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
        await model.save(update_fields=("messages_sent",))
        stages = await model.stages.filter(messages_needed=model.messages_sent)
        await asyncio.gather(
            *[self.handle_stage(stage, message.channel) for stage in stages]
        )

    @group("activitytracker", aliases=("activity", "at"), invoke_without_command=False)
    async def activity_tracker(self, ctx: Context):
        pass

    @activity_tracker.group(name="stage", aliases=("s",), invoke_without_command=False)
    async def activity_tracker_stage(self, ctx: Context):
        pass

    @check(StrataCog.mod_only)
    @activity_tracker_stage.command(name="list", aliases=("ls",))
    async def get_stages(self, ctx: Context) -> None:
        assert isinstance(ctx.author, discord.Member)
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

    @check(StrataCog.mod_only)
    @activity_tracker_stage.command(name="export", aliases=("e",))
    async def export_stages(self, ctx: Context):
        assert isinstance(ctx.author, discord.Member)
        stages = await StageModel.all()
        s = json.dumps([stage.to_dict() for stage in stages], indent=2)
        await ctx.reply(file=discord.File(BytesIO(s.encode("utf-8")), "stages.json"))

    @check(StrataCog.mod_only)
    @activity_tracker_stage.command(name="import", aliases=("i",))
    async def import_stages(self, ctx: Context):
        assert isinstance(ctx.author, discord.Member)
        await self.activity_tracker_drop(ctx)
        stages = await StageModel.all()
        s = json.dumps([stage.to_dict() for stage in stages], indent=2)
        await ctx.reply(file=discord.File(BytesIO(s.encode("utf-8")), "stages.json"))

    @check(StrataCog.mod_only)
    @activity_tracker_stage.command(name="dropall")
    async def activity_tracker_drop(self, ctx: Context) -> None:
        assert isinstance(ctx.author, discord.Member)
        await ActivityTrackerModel.select_for_update().delete()
        await ctx.send("Dropped all activity tracker data.")

    @check(StrataCog.mod_only)
    @activity_tracker_stage.group(name="add", aliases=("a",))
    async def activity_tracker_stage_add(
        self, ctx: Context, messages_needed: int, *, response_message: str
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        stage = StageModel.basic_stage(
            messages_needed=messages_needed,
            response_message=response_message,
        )
        await stage.save()
        await ctx.send(
            f"Added stage {stage.idx} :: {messages_needed} :: {response_message}"
        )

    @check(StrataCog.mod_only)
    @activity_tracker_stage_add.command(name="giveaway", aliases=("g",))
    async def add_giveaway_stage(
        self,
        ctx: Context,
        time_: TimedeltaConverter,
        messages_needed: int,
        winners: int,
        *,
        prize: str,
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        time: timedelta = time_  # type: ignore
        stage = StageModel.giveaway_stage(messages_needed, prize, winners, time)
        await stage.save()
        await ctx.send(
            f"Added giveaway stage  {stage.idx} :: {messages_needed} :: {prize} for {winners} winners"
        )

    @check(StrataCog.mod_only)
    @activity_tracker_stage.command(name="default")
    async def set_default_stage(
        self, ctx: Context, idx: int, default: bool = True
    ) -> None:
        assert isinstance(ctx.author, discord.Member)
        await StageModel.filter(idx=idx).update(default=default)
        await ctx.send(f"Added default stage :: {idx}")

    @check(StrataCog.mod_only)
    @activity_tracker_stage.command(name="enable")
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
        assert isinstance(ctx.author, discord.Member)
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
    @activity_tracker.command(name="messages_in")
    async def get_messages_in(
        self, ctx: Context, channel: Optional[discord.TextChannel] = None
    ):
        if channel is None:
            channel = ctx.channel  # type: ignore
        assert channel is not None
        if channel.id not in self.ALLOWED_CHANNELS:
            return
        assert isinstance(ctx.author, discord.Member)
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
    @activity_tracker_stage.command("remove", aliases=("r",))
    async def remove_stage(self, ctx: Context, idx: int):
        assert isinstance(ctx.author, discord.Member)
        model = await StageModel.get(idx=idx)
        await model.delete()


async def setup(bot: CustomClient):
    await bot.add_cog(ActivityTracker(bot))
