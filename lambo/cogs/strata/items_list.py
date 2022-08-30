import discord
from discord.ext.commands import Cog, Context, command
from discord.utils import escape_markdown

from lambo.main import CustomClient


class ItemsListCog(Cog, name="Items List"):
    bot: CustomClient

    ALLOWED_GUILD_IDS = [211261411119202305, 950868480041824266]

    ITEM_DICT: dict[str, str] = {
        "0kgv8fr": "Kupon zniżkowy 20%",
        "147oj1l": "Kupon zniżkowy na kanał tekstowy",
        "10bb1lc": "Kupon zniżkowy na kanał głosowy",
        "0q2fkxp": "Kupon na własne emoji",
        "0mctg0i": "Token VIP na 1 rok",
        "1jrbdb1": "Kupon zniżkowy na kanał głosowy",
        "0iw293h": "Kupon zniżkowy na kanał tekstowy",
        "0knsoy5": "Token VIP na 1 rok",
        "0szeyqt": "Token powiększenia koloru grupowego",
        "09y6ou7": "Własne emoji",
        "0iz5t42": "Token powiększenia czatu tekstowego",
        "1xegn5r": "Token ogłoszenia",
        "1t09lsj": "Gra",
        "1fzi2kc": "Token powiększenia czatu głosowego",
        "05wttpo": "Kwartalny token koloru nicku",
        "15zeds5": "Własna naklejka",
        "0fw3zc6": "Token voicechatu",
        "1spnls4": "Nitro Classic",
        "0ur75sa": "Roczny token koloru nicku",
        "1z0aklm": "Cel charytatywny",
        "0qsvs6x": "Nitro",
        "0043i99": "Giftcard",
        "1yjpmfq": "Token roli VIP!",
        "1n8izn7": "Roczny grupowy token koloru nicku",
        "1izmtrd": "Token czatu",
        "09qeh78": "Pizza",
        "1dnnwsu": "Koszulka",
    }

    def __init__(self, bot: CustomClient) -> None:
        self.bot = bot

    @command("item")
    async def get_item_name(self, ctx: Context, *, name: str):
        if ctx.guild is not None and ctx.guild.id not in self.ALLOWED_GUILD_IDS:
            return
        possible_ones: list[tuple[str, str]] = []
        for item_id, item_name in self.ITEM_DICT.items():
            if name in item_name:
                possible_ones.append((item_id, item_name))
        if not possible_ones:
            await ctx.reply("Nie znaleziono takiego przedmiotu.")
        for item_id, item_name in possible_ones:
            await ctx.send(f"`{item_id}` – {item_name}")


async def setup(bot: CustomClient):
    await bot.add_cog(ItemsListCog(bot))
