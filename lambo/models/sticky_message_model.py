

class StickyMessageModel(Model):
    channel_id: str = fields.CharField(max_length=22, unique=True)  # channel id
    bot_last_message_id: str = fields.CharField(max_length=22)  # message id
    message_content: str = fields.TextField()
