import logging
from redbot.core import commands

log = logging.getLogger("red.riddj.scrabble")

class Player():
    pass

class Board():
    pass

class Tile():

    # First value is point value, second value is number of tiles in a game
    LETTERS = {"A":(1,9), "B":(3,2), "C":(3,2), "D":(2,4), "E":(1,12), "F":(4,2), "G":(2,3), "H":(4,2), "I":(1,9), 
               "J":(8,1), "K":(5,1), "L":(1,4), "M":(3,2), "N":(1,6), "O":(1,8), "P":(3,2), "Q":(10,1), "R":(1,6), 
               "S":(1,4), "T":(1,6), "U":(1,4), "V":(4,2), "W":(4,2), "X":(8,1), "Y":(4,2), "Z":(10,1), " ":(0,2)}

    def __init__(self, letter):
        self._letter = letter

    def get_point_value(self):
        return Tile.LETTERS[self._letter[0]]
    
    def get_letter_frequency(self):
        return Tile.LETTERS[self._letter[1]]
    
    def get_letter_frequency(self, letter):
        return Tile.LETTERS[letter[1]]

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