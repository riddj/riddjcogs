import json
from pathlib import Path
from redbot.core.bot import Red
from .jisho import jisho

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]

def setup(bot):
    """ Setup jisho cog. """
    bot.add_cog(jisho(bot))