

class AddReactionModel(Model):
    channel_id: str = fields.CharField(max_length=22)  # channel id
    emoji_id: str = fields.CharField(max_length=22)  # emoji id
