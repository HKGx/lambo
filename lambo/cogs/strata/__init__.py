from typing import Callable
from lambo import CustomClient

from .activity_tracker import setup as activity_tracker_setup

# from .valentines import setup as valentines_setup
from .mention_channel import setup as mention_channel_setup
from .ping_block import setup as ping_block_setup
from .items_list import setup as items_list_setup
from .color_management import setup as color_management_setup
from .reminder import setup as reminder_setup


def apply_bot(bot: CustomClient):
    def inner(func: Callable[[CustomClient], None]) -> None:
        func(bot)

    return inner


def setup(bot: CustomClient):
    for func in (
        # valentines_setup(bot)
        # items_list_setup,
        activity_tracker_setup,
        mention_channel_setup,
        ping_block_setup,
        color_management_setup,
        reminder_setup,
    ):
        func(bot)
