import logging
from redbot.core import commands

log = logging.getLogger("red.riddj.scrabble")

class Player():
    
    def __init__(self, player=None):
        self._player = player
        self._tiles = []

    def get_tiles(self):
        return self._tiles
    
    def remove_tile(self, tile):
        self._tiles.remove(tile)

    def add_tile(self, tile):
        self._tiles.append(tile)

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
    
    def __init__(self, name, board=None):
        self._name = name
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
        self.games = {}
        self.MAXPLAYERS = 4
        self.MAXDEADTIME = 3600

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete. """
        return

    @commands.group(aliases=["sc"])
    async def scrabble(self, ctx):
        """ Create or join a game of Scrabble. """
        if ctx.invoked_subcommand is None:
            ctx.send(f"Create or join a game of scrabble using \
                     {ctx.prefix}scrabble new or {ctx.prefix}scrabble join.")
            
    @scrabble.command()
    async def new(self, ctx, name):
        """ Starts a new game of scrabble. """
        self.games[name] = Game(name)
        await ctx.send(f"Game {name} started.")

    @scrabble.command()
    async def join(self, ctx, name):
        """ Join an existing game of scrabble. """
        if ctx.author in self.games[name].get_players():
            await ctx.send(f"You're already in game {name}.")
            return
        try:
            self.games[name].add_player(ctx.author)
        except KeyError:
            await ctx.send(f"Game {name} not found.")
        else:
            await ctx.send(f"You were added to game {name}.")

    @scrabble.command()
    async def list(self, ctx):
        """ View current games of scrabble and their players. """
        if not self.games:
            await ctx.send("There are no active games of Scrabble.")
            return
        for gamename, game in self.games.items():
            gamestring = f"Game: {gamename}"
            players = f""
            for player in game.get_players():
                players += f"\n---{player}"
            if players == f"":
                players = "\n---No players yet...---"
            gamestring += players
            await ctx.send(gamestring)