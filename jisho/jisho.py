import aiohttp
import json
from redbot.core import commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

class Jisho(commands.Cog):
    """Use jisho.org for Japanese help over Discord."""

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def jisho(self, ctx, *, query: str):
        """Lookup a word or phrase on jisho.org"""
        try:
            async with ctx.typing():
                async with aiohttp.request("GET", f"https://jisho.org/api/v1/search/words?keyword={query}", headers={"Accept": "text/html"}) as r:
                    if r.status != 200:
                        return await ctx.send(f"Oops! Jisho gave a bad status - {r.status}")
                    result = await r.text(encoding="UTF-8")
                    result = json.loads(result)
        except Exception as e:
            return await ctx.send(f"Oops! Connection error! ({e, type(e)})")

        await menu(ctx, f"`{result['data'][0]['slug']}`", DEFAULT_CONTROLS)