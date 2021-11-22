import tortoise
from tortoise.models import Model
from tortoise import fields


class UsedEmojiModel(Model):
    id = fields.IntField(pk=True)
    emoji = fields.CharField(max_length=64, index=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    used_by = fields.CharField(max_length=22)  # user id
