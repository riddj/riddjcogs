import asyncio
import logging
import re
from redbot.core import commands, checks
from redbot.core.utils.predicates import MessagePredicate
from num2words import num2words

log = logging.getLogger("red.riddj.scrabble")

class Player():
    
    def __init__(self, name):
        self._name = name
        self._tiles = ["H", "E", "L", "L", "O", ".", "."]
        self._score = 0

    def get_tiles(self):
        return self._tiles
    
    def remove_tile(self, tile):
        self._tiles.remove(tile)

    def add_tile(self, tile):
        self._tiles.append(tile)

    def get_points(self):
        return self._score

    def add_points(self, points):
        self._score += points

class Tile():

    # First value is point value, second value is number of tiles in a game
    LETTERS = {"A":(1,9), "B":(3,2), "C":(3,2), "D":(2,4), "E":(1,12), "F":(4,2), "G":(2,3), "H":(4,2), "I":(1,9), 
               "J":(8,1), "K":(5,1), "L":(1,4), "M":(3,2), "N":(1,6), "O":(1,8), "P":(3,2), "Q":(10,1), "R":(1,6), 
               "S":(1,4), "T":(1,6), "U":(1,4), "V":(4,2), "W":(4,2), "X":(8,1), "Y":(4,2), "Z":(10,1), ".":(0,2)}

    def __init__(self, letter):
        self._letter = letter

    def get_point_value(self):
        return Tile.LETTERS[self._letter][0]

    def get_point_value(letter, space):
        if "LETTER" in space:
            if "DOUBLE" in space:
                return Tile.LETTERS[letter][0] * 2
            elif "TRIPLE" in space:
                return Tile.LETTERS[letter][0] * 3
        return Tile.LETTERS[letter][0]
    
    def get_letter_frequency(self):
        return Tile.LETTERS[self._letter][1]
    
    def get_letter_frequency(letter):
        return Tile.LETTERS[letter][1]

class Game():

    # {special_space_name : [[spaces], emoji_text]}, generate double word spaces in Game constructor
    SPECIAL_TILES = { "DOUBLE_WORD":[[], ":orange_square:"],
                     "TRIPLE_WORD":[[[0,0], [0,7], [0,14], [7,0],
                                     [7,14], [14,0], [14,7], [14,14]], ":red_square:"],
                     "DOUBLE_LETTER":[[[6,2], [7,3], [8,2], [6,6], [8,6], [6,8], [8,8],
                                       [3,0], [11,0], [0,3], [0,11], [14,3], [14,11],
                                       [2,6], [3,7], [2,8], [12,6], [11,7], [12,8],
                                       [6,12], [7,11], [8,12], [3,14], [11,14]], ":purple_square:"],
                     "TRIPLE_LETTER":[[[5,1], [9,1], [1,5], [13,5], [5,5], [9,9], [5,9],
                                       [9,5], [5,13], [9,13], [1,9], [13,9]], ":white_large_square:"] }
    
    def __init__(self, name):
        self._name = name
        self._players = {}
        self._joinable = True
        self._ongoing = True
        self._board = [["" for x in range(15)] for y in range(15)]
        self._board[7][7] = "START"

        # generate all 16 double word spaces
        for offset in range(3, 7):
            self._board[7 - offset][7 - offset] = \
            self._board[7 - offset][7 + offset] = \
            self._board[7 + offset][7 - offset] = \
            self._board[7 + offset][7 + offset] = "DOUBLE_WORD"

        # insert bonus point spaces
        for space_type, space_info in Game.SPECIAL_TILES.items():
            for space in space_info[0]:
                x = space[0]
                y = space[1]
                self._board[x][y] = space_type

    def get_name(self):
        return self._name

    def get_players(self):
        return self._players

    def get_tiles_by_player(self, playername):
        return self._players[playername].get_tiles()
    
    def get_board(self):
        return self._board
    
    def add_player(self, playername):
        self._players[playername] = Player(playername)

    def remove_player(self, player):
        self._players.pop(player, None)

    def can_join(self):
        return self._joinable

    def is_ongoing(self):
        return self._ongoing
    
    def end(self):
        self._ongoing = False

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
                elif space in Game.SPECIAL_TILES:
                    board_chunk += Game.SPECIAL_TILES[space][1]
                elif space == "START":
                    board_chunk += ":black_large_square:"
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
        self.debug = False

        with open("/usr/share/dict/words", "r") as words:
            self.dictionary = set(re.sub("[^\w]", " ",  words.read()).split())

    def is_word(self, word):
        return word.lower() in self.dictionary

    async def get_player_game(self, ctx):
        try:
            return self.player_active_games[ctx.author]
        except KeyError:
            await ctx.send("You aren't currently in a game!")

    async def get_game_by_name(self, ctx, gamename):
        try:
            return self.games[gamename]
        except KeyError:
            await ctx.send(f"No game with name \"{gamename}\" found.")

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete. """
        return
    
    @commands.command()
    @checks.is_owner()
    async def debug(self, ctx):
        self.debug = not self.debug
        await ctx.send(f"scrabble debug mode changed to {self.debug}.")

    @commands.group(aliases=["s"])
    async def scrabble(self, ctx):
        """ Create or join a game of Scrabble. """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Create or join a game of scrabble using " + \
                     f"{ctx.prefix}scrabble new or {ctx.prefix}scrabble join.")

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
                await ctx.send(f"You have left game {self.player_active_games[ctx.author].get_name()}.")

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
        """ Starts a game that has at least 1 player. """
        if not (game := await self.get_game_by_name(ctx, gamename)):
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
    async def end(self, ctx, gamename):
        """ Ends a game. """
        if not (game := await self.get_game_by_name(ctx, gamename)):
            return
        game.end()
        await ctx.send(f"Game {gamename} has ended.")

    @scrabble.command(aliases=["show"])
    async def print(self, ctx, gamename=None):
        """ If a gamename isn't provided, prints the board of the game you're playing. """
        if gamename is None:
            if not (game := await self.get_player_game(ctx)):
                return
        else:
            if gamename in self.games:
                game = self.games[gamename]
            else:
                await ctx.send(f"No game with name {gamename} was found.")
                return
        await ctx.send(f"Game: {game.get_name()}")
        await game.send_board(ctx)

    @scrabble.command()
    async def play(self, ctx, word, start_coord, direction):
        """ Play your letters on the board, using . or * for wild letters if you have wild tiles.
         Enter the starting coordinate with a comma between the x and y values.
         The direction is either right or down.
         i.e. `scrabble play hello 1,e right`
        """
        if not (game := await self.get_player_game(ctx)):
            return

        if not game.is_ongoing():
            await ctx.send("This game has ended.")
            return

        try:
            start_point_x, start_point_y = [int(coord, 16) for coord in start_coord.strip("()").split(",")]
            # fix double digit decimal being interpreted as hex
            if start_point_x >= 16: start_point_x -= 6
            if start_point_y >= 16: start_point_y -= 6
        except:
            await ctx.send("You didn't format your starting coordinate correctly.\n" \
                           ":white_check_mark:  3,d  :x:  3,  d  :x:  3.d  :x:  3  d")
            return
        word = word.replace("*", ".")

        # ensure player has all letter tiles in word
        if not self.debug:
            for letter in word:
                if letter.upper() not in game.get_tiles_by_player(ctx.author):
                    await ctx.send(f"You don't have all those letters!\n" \
                                f"Letters you have: {game.get_tiles_by_player(ctx.author)}")
                    return

        # handle words with wildcard characters
        if "." in word:
            await ctx.send("Please type the full word you're trying to play so that I can verify it's a real word.")
            try:
                pred = MessagePredicate.same_context(ctx)
                response = await ctx.bot.wait_for("message", timeout=10, check=pred)
                full_word = response.content
            except asyncio.TimeoutError:
                await ctx.send("No response.")
                return
            word_pieces = word.split(".")
            for piece in word_pieces:
                if piece not in full_word:
                    await ctx.send("This doesn't look like the word you initially gave me.")
                    return
    
        potentially_valid_word = word if "." not in word else full_word
        if not self.is_word(potentially_valid_word):
            await ctx.send(f"\"{potentially_valid_word}\" isn't in my dictionary of valid words.")
            return

        direction = direction.lower()[0]
        if direction not in ["r", "d"]:
            await ctx.send("Direction should be either right or down.")
            return
        if direction == "r":
            start_point = start_point_x
        else:
            start_point = start_point_y
        if len(word) + start_point > 15:
            await ctx.send("That word is too long to be played there!")
            return

        # put word on board, award points
        target_x = start_point_x
        target_y = start_point_y
        scored_points = 0
        word_multiplier = 1
        for index, letter in enumerate(word.upper()):
            if direction == "r":
                target_x = start_point_x + index
            else:
                target_y = start_point_y + index
            scored_points += Tile.get_point_value(letter, game._board[target_x][target_y])
            if "WORD" in game._board[target_x][target_y]:
                if "DOUBLE" in game._board[target_x][target_y]:
                    word_multiplier = 2
                elif "TRIPLE" in game._board[target_x][target_y]:
                    word_multiplier = 3
            game._board[target_x][target_y] = letter

        scored_points *= word_multiplier
        player = self.player_active_games[ctx.author].get_players()[ctx.author]
        player.add_points(scored_points)

        await ctx.send(f"{word} scored you {scored_points} points!\n"\
                       f"Your score is now {player.get_points()}.")
        await game.send_board(ctx)

    @scrabble.command(aliases=["pieces", "letters"])
    async def tiles(self, ctx):
        """ Shows your tiles. \".\" is a wild tile. """
        if game := await self.get_player_game(ctx):
            tiles = game.get_tiles_by_player(ctx.author)
            await ctx.send("Periods are wild.\nYour tiles:\n" + "\n".join(tiles))

    @scrabble.command(aliases=["scores"])
    async def score(self, ctx, gamename=None):
        """ Shows the score of an active game. """
        # fetch active game for player if no name provided
        if gamename is None:
            if not (game := await self.get_player_game(ctx)):
                return
        else:
            game = self.get_game_by_name(gamename)
        #await ctx.send(f"Game {type(game)}:")
        for playername, player in game.get_players().items():
            await ctx.send(f"--- {playername}: {player.get_points()} points")