from tortoise import fields
from tortoise.models import Model


class GiveawayModel(Model):
    message_id = fields.CharField(max_length=22)  # message id
    channel_id = fields.CharField(max_length=22)  # channel id
    ends_at = fields.DatetimeField()
    prize = fields.CharField(max_length=512)
    winners = fields.IntField()
    ended = fields.BooleanField(default=False)
