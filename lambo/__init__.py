__version__ = "0.1.0"


import asyncio
from discord import ExtensionFailed, ExtensionNotFound

from discord.ext.commands import errors
from tortoise import Tortoise
import tortoise.exceptions

from lambo.config import Settings
from lambo.custom_client import CustomClient

config = Settings()
bot = CustomClient(config)


async def run():
    await Tortoise.init(db_url=config.db_url, modules={"models": config.models})
    await Tortoise.generate_schemas()
    extensions = [*config.extensions, *config.non_default_extensions]
    for extension in extensions:
        bot.load_extension(extension)
        print(f"Loaded extension `{extension}`")

    await bot.start()


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except (
        KeyboardInterrupt,
        ModuleNotFoundError,
        ExtensionNotFound,
        ExtensionFailed,
        tortoise.exceptions.ConfigurationError,
    ) as e:
        print(f"{e}")
        loop.run_until_complete(Tortoise.close_connections())
        loop.run_until_complete(bot.close())
    finally:
        if loop.is_running():
            loop.close()


if __name__ == "__main__":
    main()
