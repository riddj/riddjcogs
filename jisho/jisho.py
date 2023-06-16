import json
import discord
import aiohttp
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
                    result = json.loads(result)['data']
        except Exception as e:
            return await ctx.send(f"Oops! Connection error! ({e, type(e)})")
        
        if not result:
            await ctx.send(f'There were no results for \'{query}\'.')
            return

        #await menu(ctx, f"`{result['data'][0]['slug']}`", DEFAULT_CONTROLS)
        
        # for item in result['data']:
        #     words = ''
        #     for spelling in item['japanese']:
        #         words += str(spelling)
        #     await ctx.send(words)

        # 0x56D926 is the shade of green used on jisho's website
        data = discord.Embed(description=(result[0]['japanese']), color=discord.Color(0x56D926))
        await ctx.send(embed=data)