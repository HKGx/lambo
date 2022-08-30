import asyncio

from lambo.main import CustomClient

from .activity_tracker import setup as activity_tracker_setup
from .color_management import setup as color_management_setup
from .items_list import setup as items_list_setup
# from .valentines import setup as valentines_setup
from .mention_channel import setup as mention_channel_setup
from .ping_block import setup as ping_block_setup


async def setup(bot: CustomClient):
    await asyncio.gather(
        mention_channel_setup(bot),
        ping_block_setup(bot),
        activity_tracker_setup(bot),
        items_list_setup(bot),
        color_management_setup(bot),
    )
