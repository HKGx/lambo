from datetime import timedelta
from enum import IntEnum
from tortoise import fields
from tortoise.models import Model


class ActivityTrackerModel(Model):
    channel_id = fields.CharField(max_length=22)  # channel id
    date = fields.DateField()
    messages_sent = fields.IntField(default=0)
    stages: fields.ManyToManyRelation["StageModel"] = fields.ManyToManyField(
        "lambo.StageModel", related_name="collection"
    )

    class Meta:
        unique_together = ("channel_id", "date")


class StageType(IntEnum):
    BASIC_STAGE = 1
    GIVEAWAY = 2


class StageModel(Model):
    idx = fields.IntField(pk=True)
    stage_type = fields.IntEnumField(StageType)
    messages_needed = fields.IntField()
    response_message = fields.TextField()
    default = fields.BooleanField(default=False)
    collection: fields.ReverseRelation[ActivityTrackerModel]

    winners: int = fields.IntField(null=True)
    giveaway_time: timedelta = fields.TimeDeltaField(null=True)

    def is_giveaway_stage(self) -> bool:
        if self.stage_type == StageType.GIVEAWAY:
            return True
        return False

    def is_basic_stage(self) -> bool:
        if self.stage_type == StageType.BASIC_STAGE:
            return True
        return False

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
