from lambo import CustomClient

# from .valentines import setup as valentines_setup
from .mention_channel import setup as mention_channel_setup
from .ping_block import setup as ping_block_setup


def setup(bot: CustomClient):
    # valentines_setup(bot)
    mention_channel_setup(bot)
    ping_block_setup(bot)
