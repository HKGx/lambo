from lambo.custom_client import CustomClient

from .count_emoji import setup as count_emoji_setup
from .giveaway import setup as giveaway_setup
from .moderation_utils import setup as moderation_utils_setup
from .utilities import setup as utilities_setup


def setup(bot: CustomClient) -> None:
    count_emoji_setup(bot)
    giveaway_setup(bot)
    moderation_utils_setup(bot)
    utilities_setup(bot)
