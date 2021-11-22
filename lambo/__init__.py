__version__ = '0.1.0'
import asyncio

from tortoise import Tortoise, run_async
from lambo.config import Settings
from lambo.custom_client import CustomClient
from discord.ext.commands import Bot

config = Settings()
bot = CustomClient(config)


async def run():
    await Tortoise.init(db_url=config.db_url,
                        modules={'models': ['lambo.models.used_emoji_model']})
    await Tortoise.generate_schemas()

    for extension in config.extensions:
        bot.load_extension(extension)

    await bot.start()


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        loop.run_until_complete(Tortoise.close_connections())
        loop.run_until_complete(bot.close())
    finally:
        if loop.is_running():
            loop.close()


if __name__ == '__main__':
    main()
