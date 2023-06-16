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

    async def make_embeds_from_result(self, ctx, result):
        """ Makes the embed for each word in the search results """
        async with ctx.typing():
            list_of_embeds = []
            for item in result:
                new_item = discord.Embed(description=item['japanese'][0]['reading']
                            if 'word' not in item['japanese'][0]
                            else item['japanese'][0]['word'],
                            color=discord.Color(0x56D926))
                # 0x56D926 is the shade of green used on jisho's website

                spellings = ''
                for spelling in item['japanese']:
                    spellings += str(spelling)
                new_item.add_field(name="Spellings", value=spellings)
                list_of_embeds.append(new_item)
            return list_of_embeds


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

        list_of_word_embeds = await self.make_embeds_from_result(ctx, result)
        await menu(ctx, list_of_word_embeds)