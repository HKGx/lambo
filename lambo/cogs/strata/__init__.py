from lambo import CustomClient

# from .valentines import setup as valentines_setup
from .mention_channel import setup as mention_channel_setup


def setup(bot: CustomClient):
    # valentines_setup(bot)
    mention_channel_setup(bot)
