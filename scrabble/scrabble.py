import logging
from redbot.core import commands

log = logging.getLogger("red.riddj.scrabble")

class Player():
    pass

class Board():
    pass

class Tile():
    pass

class Game():
    
    def __init__(self, board=None):
        self._board = board
        self._players = []

    def get_players(self):
        return self._players
    
    def get_board(self):
        return self._board
    
    def add_player(self, player):
        self._players.append(player)

    def remove_player(self, player):
        self._players.remove(player)

class Scrabble(commands.Cog):
    """
    Play Scrabble with your friends over discord!
    """

    def __init__(self, bot):
        self.bot = bot
        self.games = []
        self.MAXPLAYERS = 4
        self.MAXDEADTIME = 3600

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete. """
        return

    @commands.group()
    async def scrabble(self, ctx):
        """ Create or join a game of Scrabble. """
        if ctx.invoked_subcommand is None:
            ctx.send(f"Create or join a game of scrabble using \
                     {ctx.prefix}scrabble new or {ctx.prefix}scrabble join.")
            
    @scrabble.command()
    async def new(self, ctx):
        """ Starts a new game of scrabble. """
        self.games.append(Game())
        await ctx.send("NEW GAME POG")