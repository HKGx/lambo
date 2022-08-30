__version__ = "0.1.0"


import asyncio
import sys

import psycopg

from lambo.settings import Settings
from lambo.custom_client import CustomClient

config = Settings()
bot = CustomClient(config)


async def run():
    async with bot:
        # extensions = [*config.extensions, *config.non_default_extensions]
        coros = []
        for extension in []:
            coros.append(bot.load_extension(extension))
        await asyncio.gather(*coros)
        await bot.start()


# try:
# except (
#     ModuleNotFoundError,
#     ExtensionNotFound,
#     ExtensionFailed,
#     tortoise.exceptions.ConfigurationError,
# ) as e:
#     await Tortoise.close_connections()


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())


if __name__ == "__main__":
    main()
