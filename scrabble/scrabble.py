import logging
from redbot.core import commands
from num2words import num2words

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

class Tile():

    # First value is point value, second value is number of tiles in a game
    LETTERS = {"A":(1,9), "B":(3,2), "C":(3,2), "D":(2,4), "E":(1,12), "F":(4,2), "G":(2,3), "H":(4,2), "I":(1,9), 
               "J":(8,1), "K":(5,1), "L":(1,4), "M":(3,2), "N":(1,6), "O":(1,8), "P":(3,2), "Q":(10,1), "R":(1,6), 
               "S":(1,4), "T":(1,6), "U":(1,4), "V":(4,2), "W":(4,2), "X":(8,1), "Y":(4,2), "Z":(10,1), ".":(0,2)}

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
        self._board = [["" for x in range(15)] for y in range(15)]
        self._players = []
        self._joinable = True

    def get_players(self):
        return self._players
    
    def get_board(self):
        return self._board
    
    def add_player(self, player):
        self._players.append(player)

    def remove_player(self, player):
        self._players.remove(player)

    def can_join(self):
        return self._joinable
    
    def no_more_joins(self):
        self._joinable = False

    def get_header_character(self, input_character):
        if input_character < 10:
            return f":{num2words(input_character)}:"
        else:
            return f":regional_indicator_{input_character:x}:"

    async def send_board(self, ctx):
        """ Send the board to the target channel. """
        board_chunk = ""
        for header_character in range(15):
            board_chunk += self.get_header_character(header_character)
        board_chunk += "\n"
        lines = 0
        for y in range(15):
            lines += 1
            for x in range(15):
                space = self._board[x][y]
                if space == "":
                    board_chunk += ":blue_square:"
                elif space == ".":
                    board_chunk += ":asterisk:"
                else:
                    board_chunk += f":regional_indicator_{space.lower()}:"
            # Using get_header_character(y) here breaks formatting on mobile :/
            board_chunk += f" {y:x}\n"
            if lines >= 5:
                await ctx.send(board_chunk)
                lines = 0
                board_chunk = ""
        if board_chunk != "":
            await ctx.send(board_chunk)

class Scrabble(commands.Cog):
    """
    Play Scrabble with your friends over discord!
    """

    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.player_active_games = {}
        self.MAXPLAYERS = 4
        self.MAXDEADTIME = 3600

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete. """
        return

    @commands.group(aliases=["s"])
    async def scrabble(self, ctx):
        """ Create or join a game of Scrabble. """
        if ctx.invoked_subcommand is None:
            ctx.send(f"Create or join a game of scrabble using \
                     {ctx.prefix}scrabble new or {ctx.prefix}scrabble join.")
            
    @scrabble.command()
    async def new(self, ctx, name):
        """ Creates a new game of scrabble. """

        if name in self.games:
            await ctx.send("There is already a game with this name.")
            return

        self.games[name] = Game(name)
        await ctx.send(f"Game {name} created.")

    @scrabble.command()
    async def join(self, ctx, gamename):
        """ Join an existing game of scrabble. """
        try:
            game = self.games[gamename]
        except KeyError:
            await ctx.send(f"No game with name\"{gamename}\" found.")
            return

        if ctx.author in game.get_players():
            await ctx.send(f"You're already in game {gamename}.")
            return
        
        if not game.can_join():
            await ctx.send(f"You cannot join game {gamename}.")
            return
        
        if ctx.author in self.player_active_games:
            if not self.player_active_games[ctx.author].can_join():
                await ctx.send(f"You're already in an ongoing game.")
                return
            else:
                self.player_active_games[ctx.author].remove_player(ctx.author)
                await ctx.send(f"You have left game {self.player_active_games[ctx.author]._name}.")

        game.add_player(ctx.author)
        self.player_active_games[ctx.author] = game
        await ctx.send(f"You were added to game {gamename}.")

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
                players += f"\n--- {player}"
            if players == f"":
                players = "\n--- No players yet... ---"
            gamestring += players
            await ctx.send(gamestring)

    @scrabble.command()
    async def start(self, ctx, gamename):
        """ Starts a game. """
        try:
            game = self.games[gamename]
        except KeyError:
            await ctx.send(f"No game with name \"{gamename}\" found. Create a game with `{ctx.prefix}scrabble new <gamename>`.")
            return
        
        if not game.can_join():
            await ctx.send(f"Game {gamename} has already started.")
            return

        if not game.get_players():
            await ctx.send(f"There aren't any players in game {gamename} yet!")
            return
        
        game.no_more_joins()
        await ctx.send(f"Game {gamename} has started!")

    @scrabble.command()
    async def print(self, ctx, gamename):
        if gamename in self.games:
            await self.games[gamename].send_board(ctx)
        else:
            await ctx.send(f"No game with name {gamename} was found.")

    @scrabble.command()
    async def play(self, ctx, word, start_coordinate, direction):
        start_point_x = int(start_coordinate.split(",")[0], 16)
        start_point_y = int(start_coordinate.split(",")[1], 16)
        word = word.replace("*", ".")
        game = self.player_active_games[ctx.author]
        if direction.lower()[0] == "r":
            for x in range(len(word)):
                game._board[start_point_x + x][start_point_y] = word[x].upper()
        elif direction.lower()[0] == "d":
            for y in range(len(word)):
                game._board[start_point_x][start_point_y + y] = word[y].upper()
        else:
            await ctx.send("Direction should be either right or down.")
        await self.print(ctx, game._name)
