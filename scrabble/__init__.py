import json
from pathlib import Path
from redbot.core.bot import Red
from .scrabble import Scrabble

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]

def setup(bot):
    """ Setup Scrabble cog. """
    bot.add_cog(Scrabble(bot))