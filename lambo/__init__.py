__version__ = "0.1.0"


import asyncio
from discord import ExtensionFailed, ExtensionNotFound

from discord.ext.commands import errors
from prisma import Client
import prisma

from lambo.config import Settings
from lambo.custom_client import CustomClient

# Ignore type, 
config: Settings = Settings()  # type: ignore
prisma_client = Client(auto_register=True)
bot = CustomClient(config)


async def run():
    await prisma_client.connect()
    extensions = [*config.extensions, *config.non_default_extensions]
    for extension in extensions:
        try:
            bot.load_extension(extension)
            print(f"Loaded extension `{extension}`")
        except ExtensionNotFound:
            print(f"Extension {extension} not found")

    await bot.start()


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except (KeyboardInterrupt, ModuleNotFoundError, ExtensionFailed) as e:
        print(f"{e}")
        loop.run_until_complete(prisma_client.disconnect())
        loop.run_until_complete(bot.close())
    finally:
        if loop.is_running():
            loop.close()


if __name__ == "__main__":
    main()
