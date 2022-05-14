from tortoise import fields
from tortoise.models import Model


class StickyMessageModel(Model):
    channel_id = fields.CharField(max_length=22)  # channel id
    bot_last_message_id = fields.CharField(max_length=22)  # message id
    sticky_message_content = fields.TextField()
