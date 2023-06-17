import json
import discord
import aiohttp
from redbot.core import commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS, prev_page, next_page

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
            for position, item in enumerate(result):
                new_item = discord.Embed(description=item['japanese'][0]['reading']
                            if 'word' not in item['japanese'][0]
                            else item['japanese'][0]['word'],
                            color=discord.Color(0x56D926))
                # 0x56D926 is the shade of green used on jisho's website
                if item == result[-1]:
                    new_item.color = discord.Color(0xffffff)

                definitions = ''
                for number, sense in enumerate(item['senses']):
                    definitions += f'{number + 1}: '
                    for index, definition in enumerate(sense['english_definitions']):
                        definitions += definition
                        if index + 1 < len(sense['english_definitions']):
                            definitions += ', '
                    definitions += '\n'
                new_item.add_field(name="Definition", value=definitions)

                forms = ''
                for entry in item['japanese']:
                    forms += '\n'
                    if 'word' in entry:
                        forms += entry['word'] + '　-　'
                    forms += str(entry['reading'])
                new_item.add_field(name="Forms/Readings", value=forms)

                new_item.set_footer(text=f'Result {position + 1}/{len(result)}')

                list_of_embeds.append(new_item)
        return list_of_embeds


    @commands.command()
    async def jisho(self, ctx, *, query: str):
        """Lookup a word or phrase on jisho.org"""
        try:
            async with ctx.typing():
                async with aiohttp.request("GET", f"https://jisho.org/api/v1/search/words?keyword={query}", headers={"Accept": "text/html"}) as r:
                    if r.status != 200:
                        return await ctx.send(f"There was a problem reaching jisho.org. ({r.status})")
                    result = await r.text(encoding="UTF-8")
                    result = json.loads(result)['data']
        except aiohttp.ClientConnectionError:
            return await ctx.send(f"Connection error!")
        
        if not result:
            await ctx.send(f'There were no results for \'{query}\'.')
            return

        list_of_word_embeds = await self.make_embeds_from_result(ctx, result)
        left_and_right_controls_only = {
            "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}":prev_page,
            "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}":next_page
        }

        await menu(ctx, list_of_word_embeds, left_and_right_controls_only)