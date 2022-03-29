from tortoise import fields
from tortoise.models import Model


class UsedEmojiModel(Model):
    emoji = fields.CharField(max_length=64, index=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    used_by = fields.CharField(max_length=22)  # user id
