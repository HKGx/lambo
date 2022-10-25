from datetime import datetime, timedelta, date
from enum import IntEnum
from typing import Protocol, TypeGuard, TypedDict

from tortoise import fields
from tortoise.models import Model


class ActivityTrackerModel(Model):
    channel_id: str = fields.CharField(max_length=22)  # channel id
    date: date = fields.DateField()
    messages_sent: int = fields.IntField(default=0)
    stages: fields.ManyToManyRelation["StageModel"] = fields.ManyToManyField(
        "lambo.StageModel", related_name="collection"
    )

    class Meta:
        unique_together = ("channel_id", "date")


class StageType(IntEnum):
    BASIC_STAGE = 1
    GIVEAWAY = 2


class BaseStageProtocol(Protocol):
    idx: int
    stage_type: StageType
    messages_needed: int
    response_message: str
    default: bool
    collection: fields.ManyToManyRelation[ActivityTrackerModel]


class GiveawayStageProtocol(BaseStageProtocol):
    idx: int
    stage_type: StageType
    messages_needed: int
    response_message: str
    default: bool
    collection: fields.ManyToManyRelation[ActivityTrackerModel]

    winners: int
    giveaway_time: timedelta


class ExportedStageDict(TypedDict):
    idx: int
    stage_type: int
    messages_needed: int
    reponse_message: str
    default: bool
    winners: int | None
    giveaway_time: int | None


class StageModel(Model):
    idx: int = fields.IntField(pk=True)
    stage_type: StageType = fields.IntEnumField(StageType)
    messages_needed: int = fields.IntField()
    response_message: str = fields.TextField()
    default = fields.BooleanField(default=False)
    collection: fields.ReverseRelation[ActivityTrackerModel]

    winners: int | None = fields.IntField(null=True)  # only if stage_type is GIVEAWAY
    giveaway_time: timedelta | None = fields.TimeDeltaField(
        null=True
    )  # only if stage_type is GIVEAWAY

    @staticmethod
    async def export_stages_for(channel_id: str | int) -> list["StageModel"]:
        channel_id = str(channel_id)
        stages = await StageModel.filter(collection__channel_id=channel_id)
        return stages

    @classmethod
    def giveaway_stage(
        cls,
        messages_needed: int,
        giveaway_prize: str,
        winners: int,
        duration: timedelta,
    ) -> "StageModel":
        return cls(
            stage_type=StageType.GIVEAWAY,
            messages_needed=messages_needed,
            response_message=giveaway_prize,
            winners=winners,
            giveaway_time=duration,
        )

    @classmethod
    def basic_stage(cls, messages_needed: int, response_message: str) -> "StageModel":
        return cls(
            stage_type=StageType.BASIC_STAGE,
            messages_needed=messages_needed,
            response_message=response_message,
        )

    def as_dict(self) -> ExportedStageDict:
        return ExportedStageDict(
            idx=self.idx,
            stage_type=self.stage_type,
            messages_needed=self.messages_needed,
            reponse_message=self.response_message,
            default=self.default,  # type: ignore
            winners=self.winners,
            giveaway_time=(
                int(self.giveaway_time.total_seconds()) if self.giveaway_time else None
            ),  # type: ignore
        )

    @classmethod
    def from_dict(cls, data: ExportedStageDict) -> "StageModel":
        if (data["winners"] is None and data["giveaway_time"] is not None) or (
            data["winners"] is not None and data["giveaway_time"] is None
        ):
            raise ValueError("Both winners and giveaway_time must be set or not set")
        if data["stage_type"] == StageType.BASIC_STAGE:
            return cls.basic_stage(
                messages_needed=data["messages_needed"],
                response_message=data["reponse_message"],
            )
        elif data["stage_type"] == StageType.GIVEAWAY:
            return cls.giveaway_stage(
                messages_needed=data["messages_needed"],
                giveaway_prize=data["reponse_message"],
                winners=data["winners"],  # type: ignore
                duration=timedelta(seconds=data["giveaway_time"]),  # type: ignore
            )
        raise ValueError("Invalid stage type")


def is_giveaway_stage(stage: StageModel) -> TypeGuard[GiveawayStageProtocol]:
    if stage.stage_type == StageType.GIVEAWAY:
        return True
    return False


def is_basic_stage(stage: StageModel) -> TypeGuard[BaseStageProtocol]:
    if stage.stage_type == StageType.BASIC_STAGE:
        return True
    return False
