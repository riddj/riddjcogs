import json
import discord
import aiohttp
from redbot.core import commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS, prev_page, next_page, close_menu

class Jisho(commands.Cog):
    """Use jisho.org for Japanese help over Discord."""

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        return

    def __init__(self, bot):
        self.bot = bot
        self.ready_for_more_pages = False

        self.left_and_right_arrows_only = {
            '\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}':prev_page,
            '\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}':next_page
        }
        self.controls_with_next_page = {
            '\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}':prev_page,
            '\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}':next_page,
            '\u23e9':self.close_menu_and_get_more_results
        }

    def ready(self):
        self.ready_for_more_pages = True

    def not_ready(self):
        self.ready_for_more_pages = False

    def check_ready_status(self):
        return self.ready_for_more_pages

    async def close_menu_and_get_more_results(self, ctx, pages, controls, message, page, timeout, emoji):
        self.ready()
        await close_menu(ctx, pages, controls, message, page, timeout, emoji)

    async def query_jisho(self, ctx, query: str, page=1):
        """Sends a request to jisho's api for a page of results"""
        query_page = f'&page={str(page)}' if page > 1 else ''

        async with ctx.typing():
            async with aiohttp.request("GET", f"https://jisho.org/api/v1/search/words?keyword={query + query_page}", headers={"Accept": "text/html"}) as r:
                if r.status != 200:
                    await ctx.send(f"There was a problem reaching jisho.org. ({r.status})")
                    return
                result = await r.text(encoding="UTF-8")
                result = json.loads(result)['data']
            if not result:
                await ctx.send(f'There were no {"more" if page > 1 else ""} results for \'{query}\'.')
                return
        return result

    async def make_embeds_from_result(self, ctx, result, page=1):
        """ Makes the embed for each word in the search results """
        async with ctx.typing():
            list_of_embeds = []
            for position, item in enumerate(result):
                new_item = discord.Embed(description=item['japanese'][0]['reading']
                            if 'word' not in item['japanese'][0]
                            else item['japanese'][0]['word'],
                            color=discord.Color(0x56D926))
                # 0x56D926 is the shade of green used on jisho's website

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
                        forms += str(entry['word'])
                        if 'reading' in entry:
                            forms += '　-　'
                    if 'reading' in entry:
                        forms += str(entry['reading'])
                new_item.add_field(name="Forms/Readings", value=forms)

                page_info = ''
                if page > 1 or len(result) >= 20:
                    page_info = f' of Page {page}'

                new_item.set_footer(text=(f'Result {position + 1}/{len(result)}' + page_info))

                list_of_embeds.append(new_item)
        return list_of_embeds

    @commands.command()
    async def jisho(self, ctx, *, query: str):
        """Lookup a word or phrase on jisho.org"""
        try:
            result = await self.query_jisho(ctx, query)
        except aiohttp.ClientConnectionError:
            return await ctx.send(f"Connection error!")
        
        if not result:
            return

        list_of_word_embeds = await self.make_embeds_from_result(ctx, result)
        self.not_ready()
        if len(result) < 20:
            menu_controls = self.left_and_right_arrows_only
        else:
            menu_controls = self.controls_with_next_page

        await menu(ctx, list_of_word_embeds, (menu_controls if len(result) > 1 else {}))

        page = 1
        while len(result) >= 20 and self.check_ready_status():
            self.not_ready()

            page += 1
            result = await self.query_jisho(ctx, query, page)

            if not result:
                self.not_ready()
                break

            list_of_word_embeds = await self.make_embeds_from_result(ctx, result, page)

            if len(result) < 20:
                menu_controls = self.left_and_right_arrows_only
                
            await menu(ctx, list_of_word_embeds, (menu_controls if len(result) > 1 else {}))
        else:
            self.not_ready()