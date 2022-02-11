from lambo import CustomClient
from .valentines import setup as valentines_setup


def setup(bot: CustomClient):
    valentines_setup(bot)
