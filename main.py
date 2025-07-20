import discord
from discord.ext import commands
import asyncio
import os
import random
from datetime import datetime, timedelta
from discord import ui
import json
from discord.ext import commands

import asyncio
from discord.ui import Button, button, View

import time
import os
from discord.ext import commands, tasks
import time
client = commands.Bot(command_prefix=".", intents=discord.Intents.all())
client.remove_command("help")

import re
import unicodedata

# List of TOS-violating words/phrases (add more as needed)
TOS_WORDS = [
    'nigger', 'nger', 'faggot', 'fag', 'nigr',
]

# --- Global buffer for TOS multi-message detection ---
global_user_message_buffers = {}
MAX_TOS_BUFFER = max(len(word) for word in TOS_WORDS)

# Map for common letter-like emojis and regional indicators to letters
EMOJI_LETTER_MAP = {
    # Regional indicator symbols
    '🇦': 'a', '🇧': 'b', '🇨': 'c', '🇩': 'd', '🇪': 'e', '🇫': 'f', '🇬': 'g', '🇭': 'h', '🇮': 'i', '🇯': 'j',
    '🇰': 'k', '🇱': 'l', '🇲': 'm', '🇳': 'n', '🇴': 'o', '🇵': 'p', '🇶': 'q', '🇷': 'r', '🇸': 's', '🇹': 't',
    '🇺': 'u', '🇻': 'v', '🇼': 'w', '🇽': 'x', '🇾': 'y', '🇿': 'z',
    # Keycap emojis
    '🅰️': 'a', '🅱️': 'b', '🆎': 'ab', '🆑': 'cl', '🆒': 'cool', '🆓': 'free', '🆔': 'id', '🆕': 'new', '🆖': 'ng', '🆗': 'ok', '🆘': 'sos', '🆙': 'up', '🆚': 'vs',
    # Enclosed alphanumerics
    'ⓐ': 'a', 'ⓑ': 'b', 'ⓒ': 'c', 'ⓓ': 'd', 'ⓔ': 'e', 'ⓕ': 'f', 'ⓖ': 'g', 'ⓗ': 'h', 'ⓘ': 'i', 'ⓙ': 'j',
    'ⓚ': 'k', 'ⓛ': 'l', 'ⓜ': 'm', 'ⓝ': 'n', 'ⓞ': 'o', 'ⓟ': 'p', 'ⓠ': 'q', 'ⓡ': 'r', 'ⓢ': 's', 'ⓣ': 't',
    'ⓤ': 'u', 'ⓥ': 'v', 'ⓦ': 'w', 'ⓧ': 'x', 'ⓨ': 'y', 'ⓩ': 'z',
    # Add more as needed
}

# Map for leetspeak numbers to letters
LEET_MAP = {
    '1': 'i',
    '3': 'e',
    '4': 'a',
    '5': 's',
    '6': 'g',
    '7': 't',
    '0': 'o',
    '8': 'b',
}

def demojify_and_normalize(text):
    # Replace mapped emojis with their letter equivalents
    for emoji, letter in EMOJI_LETTER_MAP.items():
        text = text.replace(emoji, letter)
    # Remove all other emojis and non-spacing marks
    text = ''.join(c for c in text if c.isascii() or unicodedata.category(c)[0] != 'So')
    # Now apply the existing normalization
    return normalize(text)

def normalize(text):
    # Replace leetspeak numbers with their letter equivalents
    for leet, letter in LEET_MAP.items():
        text.replace(leet, letter)
    # Remove non-letters
    text = re.sub(r'[^a-zA-Z]', '', text)
    # Collapse all repeated letters to a single letter (e.g. niiiigggger -> niger)
    text = re.sub(r'(.)\1+', r'\1', text)
    return text.lower()

def is_subsequence(word, text):
    """Return True if all letters of word appear in order in text (subsequence match)."""
    it = iter(text)
    return all(char in it for char in word)

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

whitelist = []

def is_whitelisted():
    async def predicate(ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            return True
        guild_id = ctx.guild.id
        for entry in whitelist:
            if entry[0] == guild_id and entry[1] > time.time():
                return True
        await ctx.send("You are not whitelisted to use this command in this server.")
        return False
    return commands.check(predicate)



import random
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import View, Button

balances = {}

# Generate a hidden minefield board with one bomb
def generate_board(size=5):
    bomb_position = random.randint(0, size * size - 1)
    return bomb_position

# View for interactive buttons (the minefield)
class MineGameView(View):
    def __init__(self, ctx, bomb_position, amount):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bomb_position = bomb_position
        self.amount = amount
        self.revealed_tiles = 0
        self.size = 5  # 5x5 grid
        self.multiplier = 1.0  # Start with a base multiplier of 1.0
        self.base_multiplier = 1.24  # Starting multiplier after the first safe click
        self.active = True  # To track if the game is active (not cashed out or bomb hit)

        # Create a 5x5 grid of buttons
        for i in range(self.size * self.size):  # 25 buttons for the grid
            button = MineButton(i, bomb_position, self)
            self.add_item(button)

# Button for each tile
class MineButton(Button):
    def __init__(self, position, bomb_position, game_view):
        super().__init__(style=ButtonStyle.secondary, label="❓", row=position // 5)
        self.position = position
        self.bomb_position = bomb_position
        self.game_view = game_view

    # What happens when a button is clicked
    async def callback(self, interaction):
        if not self.game_view.active:
            return  # Game is over, do nothing

        # Ensure that only the player who started the game can click the buttons
        if interaction.user != self.game_view.ctx.author:
            await interaction.response.send_message("❌ You cannot click on this tile. It's not your game!", ephemeral=True)
            return

        if self.position == self.bomb_position:
            # User hit the bomb
            self.style = ButtonStyle.danger
            self.label = '💣'
            self.disabled = True
            await interaction.response.edit_message(content=f"💣 You hit the bomb! You lost {self.game_view.amount} coins.", view=self.game_view)

            # Deduct balance
            user_id = str(self.game_view.ctx.author.id)
            balances[user_id] -= self.game_view.amount

            # End game
            self.game_view.active = False
            # Disable all buttons
            for child in self.game_view.children:
                child.disabled = True
            await interaction.message.edit(view=self.game_view)
        else:
            # Safe click
            self.style = ButtonStyle.success
            self.label = '💎'
            self.disabled = True
            self.game_view.revealed_tiles += 1

            # Increase multiplier
            self.game_view.multiplier = round(self.game_view.base_multiplier + (self.game_view.revealed_tiles * 0.06), 2)

            # Check if user has revealed all safe tiles
            if self.game_view.revealed_tiles == (self.game_view.size * self.game_view.size - 1):
                winnings = int(self.game_view.amount * self.game_view.multiplier)
                user_id = str(self.game_view.ctx.author.id)
                balances[user_id] += winnings
                await interaction.response.edit_message(content=f"🎉 You avoided the bomb and won {winnings} coins!", view=self.game_view)

                # End game
                self.game_view.active = False
                # Disable all buttons
                for child in self.game_view.children:
                    child.disabled = True
                await interaction.message.edit(view=self.game_view)
            else:
                # Update the button in the message without completing the interaction
                await interaction.response.edit_message(view=self.game_view)

# Gamble command
@client.command()
async def gamble(ctx, amount: int):
    user = ctx.author
    user_id = str(user.id)

    # Check if user has enough balance
    if user_id not in balances:
        balances[user_id] = 1000  # Initial balance for new users

    if amount > balances[user_id]:
        await ctx.send(f"💰 You don't have enough balance to gamble {amount}. Your balance is {balances[user_id]}.")
        return

    # Generate the minefield with one bomb
    bomb_position = generate_board()

    # Create the clickable minefield using buttons
    view = MineGameView(ctx, bomb_position, amount)

    await ctx.send("💣 Mine Game Click the tiles to reveal. Avoid the bomb or use `.cashout` to claim your win!", view=view)

    # Register the active game for the user
    client.active_games[ctx.author] = view

# Cashout command
@client.command()
async def cashout(ctx):
    user_id = str(ctx.author.id)

    # Check if the user has an active game
    if ctx.author not in client.active_games:
        await ctx.send("❌ You don't have an active game to cash out!")
        return

    # Retrieve the active game
    game_view = client.active_games[ctx.author]

    # Ensure the game is still active
    if not game_view.active:
        await ctx.send("❌ Your game is over, you can't cash out now!")
        return

    # Calculate winnings
    winnings = int(game_view.amount * game_view.multiplier)
    balances[user_id] += winnings

    # Mark the game as finished
    game_view.active = False

    # Disable all buttons
    for child in game_view.children:
        child.disabled = True

    # Edit the original game message
    await game_view.ctx.send(f"💸 You cashed out and won {winnings} coins at a {game_view.multiplier}x multiplier!", view=game_view)

    # Remove the game from active games
    del client.active_games[ctx.author]

# Command to check balance
@client.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    if user_id not in balances:
        balances[user_id] = 1000  # Initial balance for new users
    await ctx.send(f"💰 Your balance is {balances[user_id]} coins.")

# Command to give coins to another user
@client.command()
async def give(ctx, member: commands.MemberConverter, amount: int):
    giver_id = str(ctx.author.id)
    receiver_id = str(member.id)

    # Check if the giver has enough balance
    if giver_id not in balances:
        balances[giver_id] = 1000  # Initial balance for new users

    if amount <= 0:
        await ctx.send("❌ You must give a positive amount!")
        return

    if amount > balances[giver_id]:
        await ctx.send(f"💰 You don't have enough balance to give {amount}. Your balance is {balances[giver_id]}.")
        return

    # Add the amount to the receiver's balance
    if receiver_id not in balances:
        balances[receiver_id] = 1000  # Initial balance for new users
    balances[giver_id] -= amount
    balances[receiver_id] += amount

    await ctx.send(f"✅ You have given {amount} coins to {member.mention}!")

# Track active games
client.active_games = {}


# Add this line to enable the command when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')




@tasks.loop(seconds=60)
async def check_whitelist_expiry():
    current_time = time.time()
    expired_entries = [entry for entry in whitelist if entry[1] <= current_time]
    for entry in expired_entries:
        whitelist.remove(entry)
        guild_id = entry[0]
        guild = client.get_guild(guild_id)
        if guild:
            owner = guild.owner
            if owner:
                try:
                    await owner.send("Your subscription to the bot whitelist has expired. Please resubscribe to continue access.")
                except discord.Forbidden:
                    print(f"Failed to send a DM to the owner of guild {guild_id}.")
        print(f"Bot removed from whitelist for guild {guild_id} due to expiration.")

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        # Check if it's the right player's turn
        game = self.view  # Reference to the TicTacToe view
        if interaction.user != game.current_player:
            await interaction.response.send_message(f"It's not your turn!", ephemeral=True)
            return

        # Update the button label and disable it
        self.label = game.current_symbol
        self.style = discord.ButtonStyle.success if game.current_symbol == "X" else discord.ButtonStyle.danger
        self.disabled = True
        game.board[self.x][self.y] = game.current_symbol

        # Check if there's a winner
        if game.check_winner(game.current_symbol):
            for button in game.children:
                button.disabled = True  # Disable all buttons when game is over
            await interaction.response.edit_message(content=f"{game.current_player.mention} wins!", view=game)
            return

        # Check if it's a draw
        if game.is_draw():
            await interaction.response.edit_message(content="It's a draw!", view=game)
            return

        # Switch turns
        game.switch_turn()
        await interaction.response.edit_message(content=f"It's {game.current_player.mention}'s turn!", view=game)

class TicTacToe(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__()
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_symbol = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]

        # Create 3x3 grid of buttons
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def switch_turn(self):
        # Switch player and symbol
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        self.current_symbol = "O" if self.current_symbol == "X" else "X"

    def check_winner(self, symbol):
        # Check rows, columns, and diagonals for a win
        for line in self.board:
            if all(cell == symbol for cell in line):
                return True
        for col in range(3):
            if all(self.board[row][col] == symbol for row in range(3)):
                return True
        if all(self.board[i][i] == symbol for i in range(3)) or all(self.board[i][2-i] == symbol for i in range(3)):
            return True
        return False

    def is_draw(self):
        # If no empty cell remains, it's a draw
        return all(cell for row in self.board for cell in row)

@client.command()
async def knock(ctx, opponent: discord.Member):
    """Start a Tic-Tac-Toe game between two players."""
    if opponent == ctx.author:
        await ctx.send("You cannot play against yourself!")
        return

    await ctx.send(f"Tic-Tac-Toe: {ctx.author.mention} vs {opponent.mention}", view=TicTacToe(ctx.author, opponent))



@client.command()
@is_whitelisted()
async def members(ctx):
    member_count = ctx.guild.member_count
    bot_count = sum(1 for member in ctx.guild.members if member.bot)
    
    non_bot_member_count = member_count - bot_count
    
    embed = discord.Embed(title="", color=0x2a2d30)
    embed.add_field(name="Humans", value=f"**Amount: {non_bot_member_count}**", inline=True)
    embed.add_field(name="Bots", value=f"**Amount: {bot_count}**", inline=True)
    embed.add_field(name="Overall", value=f"**Amount: {member_count}**", inline=True)
    
    await ctx.send(embed=embed)

@client.command()
@is_whitelisted()
async def afk(ctx, *, reason=None):
    embed = discord.Embed(color=0x2a2d30)
    now = datetime.datetime.now(datetime.timezone.utc)
    afk = True 
    start_time = int(now.timestamp())

    while afk:
        if reason is not None:
            embed.description = f'💤 {ctx.author.mention} is AFK: **{reason}** - <t:{start_time}:R>'
        else:
            embed.description = f'💤 {ctx.author.mention} is AFK: **AFK** - <t:{start_time}:R>'
        
        if "msg" not in locals():
            msg = await ctx.reply(embed=embed)
        else:
            await msg.edit(embed=embed)
        
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        
        try:
            user_msg = await client.wait_for('message', timeout=60, check=check)
            afk = False

            # Calculate how long the user was AFK
            end_time = datetime.datetime.now(datetime.timezone.utc)
            time_diff = end_time - now
            seconds = time_diff.total_seconds()

            # Format the time difference
            if seconds < 60:
                time_away = f"{int(seconds)} seconds"
            elif seconds < 3600:
                minutes = seconds // 60
                time_away = f"{int(minutes)} minutes"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                time_away = f"{int(hours)} hours and {int(minutes)} minutes"

            # Final update to the AFK message
            final_embed = discord.Embed(color=0x2a2d30)
            if reason is not None:
                final_embed.description = f'💤 {ctx.author.mention} was AFK: **{reason}** - **{time_away}**'
            else:
                final_embed.description = f'💤 {ctx.author.mention} was AFK: **AFK** - **{time_away}**'
            await msg.edit(embed=final_embed)

            # Send welcome back message
            welcome_embed = discord.Embed(color=0x2a2d30)
            welcome_embed.description = f"👋 {user_msg.author.mention} Welcome back, you were away for **{time_away}**."
            await user_msg.reply(embed=welcome_embed)
        
        except asyncio.TimeoutError:
            pass
        
        await asyncio.sleep(1)

import json
alias_file_path = "guild_aliases.json"

def load_aliases():
    try:
        with open(alias_file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

guild_aliases = load_aliases()


def save_aliases():
    with open(alias_file_path, "w") as f:
        json.dump(guild_aliases, f)


@client.command()
async def roll(ctx):
    # Generate a random number between 1 and 100
    roll_result = random.randint(1, 100)
    
    # Create an embed to show the result
    embed = discord.Embed(
        title="🎲 Dice Roll 🎲",
        description=f"{ctx.author.mention} rolled a **{roll_result}**!",
        color=0x2a2d30  # Updated color
    )
    
    # Send the embed as a response
    await ctx.send(embed=embed)



@client.command()
@commands.has_permissions(administrator=True)
async def reactions(ctx):
    """Creates a reaction roles message for Stock Robux roles"""
    
    # Create the embed
    embed = discord.Embed(
        title="💸 Reaction Roles! 💸",
        description="💰 ｜Stock\n💵 ｜Paypal\n💶 ｜Cashapp\n💴 ｜Crypto",
        color=0x2a2d30
    )
    
    # Send the message and add reactions
    message = await ctx.send(embed=embed)
    
    # Add reactions
    reactions = ['💰', '💵', '💶', '💴']
    for reaction in reactions:
        await message.add_reaction(reaction)
    
    # Store the message info for reaction handling
    guild_id = str(ctx.guild.id)
    if guild_id not in settings:
        settings[guild_id] = {}
    
    settings[guild_id]['reaction_message'] = {
        'message_id': message.id,
        'channel_id': ctx.channel.id,
        'roles': {
            '💰': 1388439272318701688,  # Stock
            '💵': 1388439272318701688,  # Paypal
            '💶': 1388439272318701688,  # Cashapp
            '💴': 1388439272318701688   # Crypto
        }
    }
    save_settings()

@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
        
    guild_id = str(payload.guild_id)
    if guild_id not in settings:
        return
        
    guild_settings = settings[guild_id]
    if 'reaction_message' not in guild_settings:
        return
        
    reaction_settings = guild_settings['reaction_message']
    if payload.message_id != reaction_settings['message_id']:
        return
        
    emoji = str(payload.emoji)
    if emoji not in reaction_settings['roles']:
        return
        
    role_id = reaction_settings['roles'][emoji]
    guild = client.get_guild(payload.guild_id)
    role = guild.get_role(role_id)
    
    if role:
        member = guild.get_member(payload.user_id)
        if member:
            await member.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == client.user.id:
        return
        
    guild_id = str(payload.guild_id)
    if guild_id not in settings:
        return
        
    guild_settings = settings[guild_id]
    if 'reaction_message' not in guild_settings:
        return
        
    reaction_settings = guild_settings['reaction_message']
    if payload.message_id != reaction_settings['message_id']:
        return
        
    emoji = str(payload.emoji)
    if emoji not in reaction_settings['roles']:
        return
        
    role_id = reaction_settings['roles'][emoji]
    guild = client.get_guild(payload.guild_id)
    role = guild.get_role(role_id)
    
    if role:
        member = guild.get_member(payload.user_id)
        if member:
            await member.remove_roles(role)

@client.command()
@is_whitelisted()
async def react(ctx, *, message_content: str):
    title = None
    description = None
    if "(" in message_content and ")" in message_content:
        start_index = message_content.index("(")
        end_index = message_content.index(")")
        title = message_content[start_index + 1: end_index]
        description = message_content[:start_index] + message_content[end_index + 1:]
    else:
        description = message_content

    message_parts = description.split(" ")
    emoji_input = message_parts[-2]
    role_id = int(message_parts[-1])
    message_text = " ".join(message_parts[:-2])
    role = ctx.guild.get_role(role_id)
    if role is None:
        await ctx.send("Invalid role ID.")
        return

    custom_emoji = None
    if emoji_input.startswith("<") and emoji_input.endswith(">"):
        emoji_id = int(emoji_input.split(":")[-1][:-1])
        custom_emoji = discord.utils.get(ctx.guild.emojis, id=emoji_id)
    else:
        custom_emoji = discord.utils.get(ctx.guild.emojis, name=emoji_input.strip(':'))

    if custom_emoji is None:
        await ctx.send("Invalid emoji.")
        return

    embed = discord.Embed(description=message_text, color=0x2a2d30)
    if title:
        embed.title = title

    # Send the embed
    embed_message = await ctx.send(embed=embed)

    # Add reaction to the embed message
    await embed_message.add_reaction(custom_emoji)

    while True:
        # Define reaction check function
        def check(reaction, user):
            return str(reaction.emoji) == str(custom_emoji) and reaction.message.id == embed_message.id

        # Wait for reaction
        reaction, user = await client.wait_for('reaction_add', check=check)

        # Assign role to the user
        await user.add_roles(role)

        # Define unreaction check function
        def uncheck(reaction, user):
            return str(reaction.emoji) == str(custom_emoji) and reaction.message.id == embed_message.id

        # Wait for unreaction
        reaction, user = await client.wait_for('reaction_remove', check=uncheck)

        # Remove role from the user
        await user.remove_roles(role)


@client.event
async def on_interaction(interaction):
    if isinstance(interaction, discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            await client.process_commands(interaction)
        # Remove custom dropdown dispatch
        # elif interaction.type == discord.InteractionType.component:
        #     client.dispatch('dropdown', interaction)

class LockButton(View):
    def __init__(self, channel=None):
        super().__init__(timeout=None)
        self.channel = channel
    
    lock_button_style = discord.ButtonStyle.secondary
    unlock_button_style = discord.ButtonStyle.secondary
    ghost_button_style = discord.ButtonStyle.secondary
    reveal_button_style = discord.ButtonStyle.secondary
    claim_button_style = discord.ButtonStyle.secondary
    view_button_style = discord.ButtonStyle.secondary
    plus_button_style = discord.ButtonStyle.secondary
    minus_button_style = discord.ButtonStyle.secondary
    disconnect_button_style = discord.ButtonStyle.secondary
    
    @button(label="🔒", style=lock_button_style, custom_id="lock_vc")
    async def lock_vc(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._lock_action)

    @button(label="🔓", style=unlock_button_style, custom_id="unlock_vc")
    async def unlock_vc(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._unlock_action)

    @button(label="👻", style=ghost_button_style, custom_id="ghost_vc")
    async def ghost_vc(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._ghost_action)
    
    @button(label="🔍", style=reveal_button_style, custom_id="reveal_vc")
    async def reveal_vc(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._reveal_action)
    
    @button(label="🔑", style=claim_button_style, custom_id="claim_vc")
    async def claim_vc(self, interaction: discord.Interaction, button: Button):
        await self._claim_action(interaction, interaction.user.voice.channel)
    
    @button(label="👢", style=disconnect_button_style, custom_id="disconnect_button")
    async def disconnect_button(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._disconnect_action)
    
    @button(label="ℹ️", style=view_button_style, custom_id="view_vc")
    async def view_vc(self, interaction: discord.Interaction, button: Button):
        voice_channel = interaction.user.voice.channel
        await self._view_action(interaction, voice_channel)

    @button(label="➕", style=plus_button_style, custom_id="increase_limit_vc")
    async def increase_limit_vc(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._increase_limit_action)
        
    @button(label="➖", style=minus_button_style, custom_id="decrease_limit_vc")
    async def decrease_limit_vc(self, interaction: discord.Interaction, button: Button):
        await self._check_and_execute(interaction, self._decrease_limit_action)
        
    async def _check_and_execute(self, interaction, action):
        if interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.response.send_message(embed=discord.Embed(description="You are not in a voice channel."), ephemeral=True)
            return
        
        voice_channel = interaction.user.voice.channel
        
        if not voice_channel.name.startswith(interaction.user.name) and action != self._claim_action:
            await interaction.response.send_message(embed=discord.Embed(description="You do not own this voice channel."), ephemeral=True)
            return
        
        await action(interaction, voice_channel)
    
    async def _lock_action(self, interaction, voice_channel):
        await voice_channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} has been locked."), ephemeral=True)
    
    async def _unlock_action(self, interaction, voice_channel):
        await voice_channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} has been unlocked."), ephemeral=True)
    
    async def _ghost_action(self, interaction, voice_channel):
        await voice_channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} is now hidden."), ephemeral=True)
    
    async def _reveal_action(self, interaction, voice_channel):
        await voice_channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} is now revealed to everyone."), ephemeral=True)
    
    async def _claim_action(self, interaction, voice_channel):
        current_owner = await self._get_owner(voice_channel)
        if current_owner and current_owner in voice_channel.members:
            await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} is already claimed by {current_owner.display_name}."), ephemeral=True)
            return
        
        await voice_channel.edit(name=f"{interaction.user.name}'s Channel")
        await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} has been claimed by {interaction.user.display_name}."), ephemeral=True)
    
    async def _view_action(self, interaction, voice_channel):
        owner = await self._get_owner(voice_channel)
        owner_info = f"**Owner:** `{owner.display_name} ({owner.id})`" if owner else "**Owner:** `No owner found.`"
        
        locked_emoji = "❌"
        unlocked_emoji = "✅"
        
        lock_status = locked_emoji if voice_channel.overwrites_for(interaction.guild.default_role).connect else unlocked_emoji
        locked_info = f"**Locked:** {lock_status}"
        
        limit_info = f"**Limit:** `{voice_channel.user_limit}`" if voice_channel.user_limit else "**Limit:** `0`"
        
        bitrate_info = f"**Bitrate:** `{voice_channel.bitrate / 1000} kbps`"
        
        connected_info = f"**Connected:** `{len(voice_channel.members)}`"
        
        
        embed = discord.Embed(title=f"{voice_channel.name} Details")
        embed.add_field(name="Voice Channel Information", value=f"{owner_info}\n{locked_info}\n{limit_info}\n{bitrate_info}\n{connected_info}", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _increase_limit_action(self, interaction, voice_channel):
        if voice_channel.user_limit is None:
            await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} does not have a limit set."), ephemeral=True)
            return
        
        await voice_channel.edit(user_limit=voice_channel.user_limit + 1)
        await interaction.response.send_message(embed=discord.Embed(description=f"Limit for {voice_channel.name} increased to {voice_channel.user_limit + 1}."), ephemeral=True)
    
    async def _decrease_limit_action(self, interaction, voice_channel):
        if voice_channel.user_limit is None:
            await interaction.response.send_message(embed=discord.Embed(description=f"{voice_channel.name} does not have a limit set."), ephemeral=True)
            return
        
        await voice_channel.edit(user_limit=max(0, voice_channel.user_limit - 1))
        await interaction.response.send_message(embed=discord.Embed(description=f"Limit for {voice_channel.name} decreased to {max(0, voice_channel.user_limit - 1)}."), ephemeral=True)
    
    async def _disconnect_action(self, interaction, voice_channel):
        if not voice_channel.name.startswith(interaction.user.name):
            embed = discord.Embed(description="You do not own this voice channel.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        options = [discord.SelectOption(label=f"{member.display_name} ({member.id})", value=str(member.id)) for member in voice_channel.members]
        select = discord.ui.Select(placeholder="Choose a user to disconnect", options=options, custom_id="disconnect_dropdown")
        view = discord.ui.View()
        view.add_item(select)
        
        mention = interaction.user.mention
        embed = discord.Embed(description=f"{mention}, select a user to disconnect:")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _get_owner(self, voice_channel):
        for member in voice_channel.members:
            if voice_channel.name.startswith(member.name):
                return member
        return None

@client.command(name="reject", aliases=["vc reject"])
@is_whitelisted()
async def vc_reject(ctx, *, user_input):
    try:
        user_id = int(user_input)
        user = ctx.guild.get_member(user_id)
    except ValueError:
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = discord.utils.get(ctx.guild.members, name=user_input)
    
    if user is None:
        await ctx.send(embed=discord.Embed(description="User not found."), ephemeral=True)
        return
    
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send(embed=discord.Embed(description="You are not in a voice channel."), ephemeral=True)
        return
    
    voice_channel = ctx.author.voice.channel
    
    if not voice_channel.name.startswith(ctx.author.name):
        await ctx.send(embed=discord.Embed(description="You do not own this voice channel."), ephemeral=True)
        return
    
    await voice_channel.set_permissions(user, connect=False)
    await ctx.send(embed=discord.Embed(description=f"{user.display_name} has been rejected from {voice_channel.name}."), ephemeral=True)
    
@client.command(name="permit")
@is_whitelisted()
async def permit(ctx, *, user_input):
    try:
        user_id = int(user_input)
        user = ctx.guild.get_member(user_id)
    except ValueError:
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = discord.utils.get(ctx.guild.members, name=user_input)
    
    if user is None:
        await ctx.send(embed=discord.Embed(description="User not found."), ephemeral=True)
        return
    
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send(embed=discord.Embed(description="You are not in a voice channel."), ephemeral=True)
        return
    
    voice_channel = ctx.author.voice.channel
    
    if not voice_channel.name.startswith(ctx.author.name):
        await ctx.send(embed=discord.Embed(description="You do not own this voice channel."), ephemeral=True)
        return
    
    await voice_channel.set_permissions(user, connect=True)
    await ctx.send(embed=discord.Embed(description=f"{user.display_name} has been permitted to join {voice_channel.name}."), ephemeral=True)

@client.command()
@is_whitelisted()
@commands.has_permissions(manage_channels=True)
async def mute(ctx, *, user_input):
    try:
        # Try parsing user_input as an integer (user ID)
        user_id = int(user_input)
        user = ctx.guild.get_member(user_id)
    except ValueError:
        # If parsing fails, user_input is not an integer, try mentioning a user or searching by username
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            # Try finding user by username
            user = discord.utils.get(ctx.guild.members, name=user_input)
    
    if user is None:
        await ctx.send(embed=discord.Embed(description="User not found."), ephemeral=True)
        return
    
    # Loop through all channels in the guild
    for channel in ctx.guild.channels:
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(user, send_messages=False)
    
    await ctx.send(embed=discord.Embed(description=f"{user.display_name} has been muted in all channels."), ephemeral=True)


@client.command()
@is_whitelisted()
@commands.has_permissions(manage_channels=True)
async def unmute(ctx, *, user_input):
    try:
        # Try parsing user_input as an integer (user ID)
        user_id = int(user_input)
        user = ctx.guild.get_member(user_id)
    except ValueError:
        # If parsing fails, user_input is not an integer, try mentioning a user or searching by username
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            # Try finding user by username
            user = discord.utils.get(ctx.guild.members, name=user_input)
    
    if user is None:
        await ctx.send(embed=discord.Embed(description="User not found."), ephemeral=True)
        return
    
    # Loop through all channels in the guild
    for channel in ctx.guild.channels:
        if isinstance(channel, discord.TextChannel):
            # Remove user-specific permissions for the channel
            await channel.set_permissions(user, overwrite=None)
    
    await ctx.send(embed=discord.Embed(description=f"{user.display_name} has been unmuted in all channels."), ephemeral=True)

@client.command()
@is_whitelisted()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, *, whitelist_role_id=None):
    await ctx.message.delete()
    channel = ctx.channel
    
    whitelist_role = None
    
    if whitelist_role_id:
        try:
            role_id = int(whitelist_role_id)
            whitelist_role = discord.utils.get(ctx.guild.roles, id=role_id)
        except ValueError:
            whitelist_role = discord.utils.get(ctx.guild.roles, name=whitelist_role_id)
    if ctx.author.guild_permissions.manage_channels:
        await channel.set_permissions(ctx.author, send_messages=True)
    
    # Lock the channel by revoking send message permissions for everyone
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    
    # If a whitelist role is provided, allow users with that role to send messages
    if whitelist_role:
        await channel.set_permissions(whitelist_role, send_messages=True)
        await ctx.send(embed=discord.Embed(description=f"This channel has been locked. Only users with the role **{whitelist_role.name}** can send messages now."), ephemeral=True)
    else:
        await ctx.send(embed=discord.Embed(description="This channel has been locked. Only administrators can send messages now."), ephemeral=True)

@client.command()
@is_whitelisted()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if not ctx.guild.me.guild_permissions.kick_members:
        embed = discord.Embed(title="Permission Error", description="I don't have permission to kick members.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(title="Member Kicked", description=f"{member.mention} has been kicked.", color=discord.Color.default())
        message = await ctx.send(embed=embed)

        if kick_logs_channel is not None:
            log_embed = discord.Embed(title="Kicked Member",  color=discord.Color.default())
            log_embed.add_field(name="Kicked User", value=member.mention, inline=True)
            log_embed.add_field(name="Kicked By", value=ctx.author.mention, inline=True)
            log_embed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=True)
            await kick_logs_channel.send(embed=log_embed)

        await asyncio.sleep(3)
        await message.delete()
    except discord.Forbidden:
        embed = discord.Embed(title="Permission Error", description="I don't have permission to kick this member.", color=discord.Color.red())
        await ctx.send(embed=embed)
    except discord.HTTPException:
        embed = discord.Embed(title="Error", description="Kicking failed due to an error.", color=discord.Color.red())
        await ctx.send(embed=embed)

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="Error", description="Invalid member specified.", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="Error", description="Missing required argument: member.", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="Permission Error", description="You don't have permission to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed)




@client.command()
@is_whitelisted()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.message.delete()
    channel = ctx.channel
    
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    
    await ctx.send(embed=discord.Embed(description="This channel has been unlocked. Everyone can send messages now."), ephemeral=True)

@client.command()
@is_whitelisted()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    # Get the current channel
    channel = ctx.channel
    
    # Duplicate the channel
    new_channel = await channel.clone()
    
    # Get the position of the original channel
    position = channel.position
    
    # Delete the original channel
    await channel.delete()
    
    # Send an embedded message in the new channel
    embed = discord.Embed(description="This channel has been duplicated.")
    message = await new_channel.send(embed=embed)
    
    # Wait for 5 seconds
    await asyncio.sleep(5)
    
    # Delete the message after 5 seconds
    await message.delete()
    
    await ctx.send(embed=discord.Embed(description=f"The channel has been nuked. A new channel named **{new_channel.name}** has been created."), ephemeral=True)



ticket_count = 0 
claim_notification_channel_id = None
claim_counts = {}

# --- Ticket Dropdown Persistent View ---
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="📩 General Support", value="option_1"),
            discord.SelectOption(label="📝 Staff Application", value="option_2"),
            discord.SelectOption(label="🚨 Staff Report", value="option_3"),
            discord.SelectOption(label="🔓 Ban Appeal", value="option_4"),
            discord.SelectOption(label="💸 Donation Ticket", value="option_5"),
        ]
        super().__init__(placeholder="Make a selection", options=options, custom_id="ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        category_id_option_1 = 1388439413612216390
        category_id_option_2 = 1388439413612216390
        category_id_option_3 = 1388439413612216390
        category_id_option_4 = 1388439413612216390
        category_id_option_5 = 1388439413612216390
        selected_option = self.values[0]
        try:
            if selected_option == "option_1":
                modal = SupportModal(category_id_option_1)
                await interaction.response.send_modal(modal)
            elif selected_option == "option_2":
                modal = StaffApplicationModal(category_id_option_2)
                await interaction.response.send_modal(modal)
            elif selected_option == "option_3":
                modal = StaffReportModal(category_id_option_3)
                await interaction.response.send_modal(modal)
            elif selected_option == "option_4":
                modal = BanAppealModal(category_id_option_4)
                await interaction.response.send_modal(modal)
            elif selected_option == "option_5":
                modal = DonationModal(category_id_option_5)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Invalid option selected.", ephemeral=True)
        except Exception as e:
            print(f"Error sending modal: {e}")

class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# --- Update tickets command to use the new persistent view ---
@client.command()
async def tickets(ctx):
    view = TicketDropdownView()
    embed = discord.Embed(title="Support Ticket", description="Select the drop down to create a ticket.")
    embed.set_footer(text="Ticket system")
    await ctx.send(embed=embed, view=view)

@client.command()
@is_whitelisted()
async def help(ctx):
    view = discord.ui.View()
    options = [
        discord.SelectOption(label="🔨 Moderation", value="helpp_option_1"),
        discord.SelectOption(label="👥 Everyone", value="helpp_option_2"),
        discord.SelectOption(label="🚀 Booster", value="helpp_option_3")
    ]
    select = discord.ui.Select(placeholder="Make a selection", options=options, custom_id="helpp_dropdown")
    view.add_item(select)
    
    embed = discord.Embed(title="Help Categories", description="Select the drop down to choose a help category.")
    embed.set_footer(text="Help system")
    
    await ctx.send(embed=embed, view=view)

class SupportModal(discord.ui.Modal, title='General Support Ticket'):
    def __init__(self, category_id):
        super().__init__()
        self.category_id = category_id
        self.issue = discord.ui.TextInput(
            label="What's your issue?",
            placeholder="Describe your problem in detail",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=1,
            max_length=1000
        )
        self.attempted_solutions = discord.ui.TextInput(
            label="Have you tried any solutions?",
            placeholder="List any solutions you've already tried",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=1,
            max_length=1000
        )
        self.add_item(self.issue)
        self.add_item(self.attempted_solutions)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            global ticket_count
            guild = interaction.guild
            print(f"[DEBUG] SupportModal: Trying to fetch category with ID: {self.category_id}")
            category = await interaction.guild.fetch_channel(self.category_id)
            print(f"[DEBUG] SupportModal: Fetched category: {category} (type: {type(category)})")
            
            try:
                category = await interaction.guild.fetch_channel(self.category_id)
                await interaction.response.send_message(
                    f"Fetched: {category} (type: {type(category)}) | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.response.send_message(
                    f"Error fetching category: {e} | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            
            if category is None or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("Provided ID is not a category channel.", ephemeral=True)
                return

            staff_role_id = 1388439296813437049
            staff_role = interaction.guild.get_role(staff_role_id)
            member = interaction.user

            ticket_count += 1
            ticket_number = str(ticket_count).zfill(4)
            
            # Create channel name using ticket number
            channel_name = f"ticket-{ticket_number}"
            
            # Set up permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if staff_role is not None:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            # Create the ticket channel
            ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)

            # Create embed with ticket information
            embed = discord.Embed(
                title=f"Support Ticket - #{ticket_number}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Requested By", value=interaction.user.mention, inline=False)
            embed.add_field(name="Issue", value=self.issue.value, inline=False)
            embed.add_field(name="Attempted Solutions", value=self.attempted_solutions.value, inline=False)

            # Add buttons
            claim_button = ClaimButton(member, staff_role)
            close_button = CloseButton()
            transcript_button = TranscriptButton()
            
            view = discord.ui.View(timeout=None)
            view.add_item(claim_button)
            view.add_item(close_button)
            view.add_item(transcript_button)

            # Send messages
            await ticket_channel.send(embed=embed, view=view)
            await ticket_channel.send(f"{member.mention}")
            await interaction.response.send_message(f"Ticket channel {ticket_channel.mention} has been created in {category.mention}.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while creating your ticket: {str(e)}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while processing your ticket. Please try again.", ephemeral=True)

class StaffApplicationModal(discord.ui.Modal, title='Staff Application'):
    def __init__(self, category_id):
        super().__init__()
        self.category_id = category_id
        self.why_staff = discord.ui.TextInput(
            label="Why do you want to be staff?",
            placeholder="Explain your motivation...",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500
        )
        self.why_fit = discord.ui.TextInput(
            label="Why do you think you're a good fit?",
            placeholder="Describe your skills or experience...",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500
        )
        self.add_item(self.why_staff)
        self.add_item(self.why_fit)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            global ticket_count
            guild = interaction.guild
            print(f"[DEBUG] StaffApplicationModal: Trying to fetch category with ID: {self.category_id}")
            category = await interaction.guild.fetch_channel(self.category_id)
            print(f"[DEBUG] StaffApplicationModal: Fetched category: {category} (type: {type(category)})")
            
            try:
                category = await interaction.guild.fetch_channel(self.category_id)
                await interaction.response.send_message(
                    f"Fetched: {category} (type: {type(category)}) | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.response.send_message(
                    f"Error fetching category: {e} | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            
            if category is None or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("Provided ID is not a category channel.", ephemeral=True)
                return

            staff_role_id = 1388439296813437049
            staff_role = interaction.guild.get_role(staff_role_id)
            member = interaction.user

            ticket_count += 1
            ticket_number = str(ticket_count).zfill(4)
            
            # Create channel name using ticket number
            channel_name = f"staff-app-{ticket_number}"
            
            # Set up permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if staff_role is not None:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            # Create the ticket channel
            ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)

            # Create embed with application information
            embed = discord.Embed(
                title=f"Staff Application - #{ticket_number}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Applicant", value=interaction.user.mention, inline=False)
            embed.add_field(name="Why do you want to be staff?", value=self.why_staff.value, inline=False)
            embed.add_field(name="Why are you a good fit?", value=self.why_fit.value, inline=False)

            # Add buttons
            claim_button = ClaimButton(member, staff_role)
            close_button = CloseButton()
            transcript_button = TranscriptButton()
            
            view = discord.ui.View(timeout=None)
            view.add_item(claim_button)
            view.add_item(close_button)
            view.add_item(transcript_button)

            # Send messages
            await ticket_channel.send(embed=embed, view=view)
            await ticket_channel.send(f"{member.mention}")
            await interaction.response.send_message(f"Staff application channel {ticket_channel.mention} has been created in {category.mention}.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while creating your application: {str(e)}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while processing your application. Please try again.", ephemeral=True)

# --- Staff Report Modal ---
class StaffReportModal(discord.ui.Modal, title='Staff Report'):
    def __init__(self, category_id):
        super().__init__()
        self.category_id = category_id
        self.staff_user = discord.ui.TextInput(
            label="Username of the staff you want to report",
            placeholder="Enter staff username or @mention",
            required=True,
            style=discord.TextStyle.short,
            min_length=2,
            max_length=100
        )
        self.reason = discord.ui.TextInput(
            label="Why do you want to report them?",
            placeholder="Describe the issue...",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500
        )
        self.add_item(self.staff_user)
        self.add_item(self.reason)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            global ticket_count
            guild = interaction.guild
            print(f"[DEBUG] StaffReportModal: Trying to fetch category with ID: {self.category_id}")
            category = await interaction.guild.fetch_channel(self.category_id)
            print(f"[DEBUG] StaffReportModal: Fetched category: {category} (type: {type(category)})")
            
            try:
                category = await interaction.guild.fetch_channel(self.category_id)
                await interaction.response.send_message(
                    f"Fetched: {category} (type: {type(category)}) | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.response.send_message(
                    f"Error fetching category: {e} | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            
            if category is None or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("Provided ID is not a category channel.", ephemeral=True)
                return

            staff_role_id = 1388439296813437049
            staff_role = interaction.guild.get_role(staff_role_id)
            member = interaction.user
            ticket_count += 1
            ticket_number = str(ticket_count).zfill(4)
            channel_name = f"staff-report-{ticket_number}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if staff_role is not None:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)
            embed = discord.Embed(
                title=f"Staff Report - #{ticket_number}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Reporter", value=interaction.user.mention, inline=False)
            embed.add_field(name="Staff User Reported", value=self.staff_user.value, inline=False)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)
            claim_button = ClaimButton(member, staff_role)
            close_button = CloseButton()
            transcript_button = TranscriptButton()
            view = discord.ui.View(timeout=None)
            view.add_item(claim_button)
            view.add_item(close_button)
            view.add_item(transcript_button)
            await ticket_channel.send(embed=embed, view=view)
            await ticket_channel.send(f"{member.mention}")
            await interaction.response.send_message(f"Staff report channel {ticket_channel.mention} has been created in {category.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while creating your report: {str(e)}", ephemeral=True)
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while processing your report. Please try again.", ephemeral=True)

# --- Ban Appeal Modal ---
class BanAppealModal(discord.ui.Modal, title='Ban Appeal'):
    def __init__(self, category_id):
        super().__init__()
        self.category_id = category_id
        self.banned_user = discord.ui.TextInput(
            label="User that got banned",
            placeholder="Enter username or user ID",
            required=True,
            style=discord.TextStyle.short,
            min_length=2,
            max_length=100
        )
        self.why_unban = discord.ui.TextInput(
            label="Why should they be unbanned?",
            placeholder="Explain why you think the ban should be lifted...",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500
        )
        self.add_item(self.banned_user)
        self.add_item(self.why_unban)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            global ticket_count
            guild = interaction.guild
            print(f"[DEBUG] BanAppealModal: Trying to fetch category with ID: {self.category_id}")
            category = await interaction.guild.fetch_channel(self.category_id)
            print(f"[DEBUG] BanAppealModal: Fetched category: {category} (type: {type(category)})")
            
            try:
                category = await interaction.guild.fetch_channel(self.category_id)
                await interaction.response.send_message(
                    f"Fetched: {category} (type: {type(category)}) | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.response.send_message(
                    f"Error fetching category: {e} | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            
            if category is None or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("Provided ID is not a category channel.", ephemeral=True)
                return

            staff_role_id = 1388439296813437049
            staff_role = interaction.guild.get_role(staff_role_id)
            member = interaction.user
            ticket_count += 1
            ticket_number = str(ticket_count).zfill(4)
            channel_name = f"ban-appeal-{ticket_number}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if staff_role is not None:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)
            embed = discord.Embed(
                title=f"Ban Appeal - #{ticket_number}",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Applicant", value=interaction.user.mention, inline=False)
            embed.add_field(name="Banned User", value=self.banned_user.value, inline=False)
            embed.add_field(name="Why Unban?", value=self.why_unban.value, inline=False)
            claim_button = ClaimButton(member, staff_role)
            close_button = CloseButton()
            transcript_button = TranscriptButton()
            view = discord.ui.View(timeout=None)
            view.add_item(claim_button)
            view.add_item(close_button)
            view.add_item(transcript_button)
            await ticket_channel.send(embed=embed, view=view)
            await ticket_channel.send(f"{member.mention}")
            await interaction.response.send_message(f"Ban appeal channel {ticket_channel.mention} has been created in {category.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while creating your appeal: {str(e)}", ephemeral=True)
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while processing your appeal. Please try again.", ephemeral=True)

# --- Donation Modal ---
class DonationModal(discord.ui.Modal, title='Donation Ticket'):
    def __init__(self, category_id):
        super().__init__()
        self.category_id = category_id
        self.amount = discord.ui.TextInput(
            label="How much would you like to donate?",
            placeholder="Enter amount (e.g. $10, $50, etc.)",
            required=True,
            style=discord.TextStyle.short,
            min_length=1,
            max_length=100
        )
        self.reason = discord.ui.TextInput(
            label="Why are you donating?",
            placeholder="Let us know your motivation or if you want anything special!",
            required=True,
            style=discord.TextStyle.paragraph,
            min_length=5,
            max_length=300
        )
        self.add_item(self.amount)
        self.add_item(self.reason)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            global ticket_count
            guild = interaction.guild
            print(f"[DEBUG] DonationModal: Trying to fetch category with ID: {self.category_id}")
            category = await interaction.guild.fetch_channel(self.category_id)
            print(f"[DEBUG] DonationModal: Fetched category: {category} (type: {type(category)})")
            
            try:
                category = await interaction.guild.fetch_channel(self.category_id)
                await interaction.response.send_message(
                    f"Fetched: {category} (type: {type(category)}) | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.response.send_message(
                    f"Error fetching category: {e} | Guild: {interaction.guild} (ID: {interaction.guild.id}) | Category ID: {self.category_id}",
                    ephemeral=True
                )
                return
            
            if category is None or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("Provided ID is not a category channel.", ephemeral=True)
                return

            staff_role_id = 1388439296813437049
            staff_role = interaction.guild.get_role(staff_role_id)
            member = interaction.user
            ticket_count += 1
            ticket_number = str(ticket_count).zfill(4)
            channel_name = f"donation-{ticket_number}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if staff_role is not None:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)
            embed = discord.Embed(
                title=f"Donation Ticket - #{ticket_number}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Donor", value=interaction.user.mention, inline=False)
            embed.add_field(name="Donation Amount", value=self.amount.value, inline=False)
            embed.add_field(name="Reason for Donating", value=self.reason.value, inline=False)
            claim_button = ClaimButton(member, staff_role)
            close_button = CloseButton()
            transcript_button = TranscriptButton()
            view = discord.ui.View(timeout=None)
            view.add_item(claim_button)
            view.add_item(close_button)
            view.add_item(transcript_button)
            await ticket_channel.send(embed=embed, view=view)
            await ticket_channel.send(f"{member.mention}")
            await interaction.response.send_message(f"Donation ticket channel {ticket_channel.mention} has been created in {category.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while creating your donation ticket: {str(e)}", ephemeral=True)
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while processing your donation ticket. Please try again.", ephemeral=True)

# --- Update Dropdown ---
@client.event
async def on_dropdown(interaction: discord.Interaction):
    global ticket_count
    if interaction.data["custom_id"] == "ticket_dropdown":
        selected_option = interaction.data["values"][0]
        category_id_option_1 = 1388439413612216390
        category_id_option_2 = 1388439413612216390
        category_id_option_3 = 1388439413612216390
        category_id_option_4 = 1388439413612216390
        category_id_option_5 = 1388439413612216390
        if selected_option == "option_2":
            try:
                modal = StaffApplicationModal(category_id_option_2)
                await interaction.response.send_modal(modal)
                return
            except Exception as e:
                print(f"Error sending modal: {e}")
                return
        if selected_option == "option_1":
            try:
                modal = SupportModal(category_id_option_1)
                await interaction.response.send_modal(modal)
                return
            except Exception as e:
                print(f"Error sending modal: {e}")
                return
        if selected_option == "option_3":
            try:
                modal = StaffReportModal(category_id_option_3)
                await interaction.response.send_modal(modal)
                return
            except Exception as e:
                print(f"Error sending modal: {e}")
                return
        if selected_option == "option_4":
            try:
                modal = BanAppealModal(category_id_option_4)
                await interaction.response.send_modal(modal)
                return
            except Exception as e:
                print(f"Error sending modal: {e}")
                return
        if selected_option == "option_5":
            try:
                modal = DonationModal(category_id_option_5)
                await interaction.response.send_modal(modal)
                return
            except Exception as e:
                print(f"Error sending modal: {e}")
                return
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message("Invalid option selected.", ephemeral=True)
            else:
                await interaction.followup.send("Invalid option selected.", ephemeral=True)
            return
        await asyncio.sleep(2)
        view = discord.ui.View()
        options = [
            discord.SelectOption(label="📩 General Support", value="option_1"),
            discord.SelectOption(label="📝 Staff Application", value="option_2"),
            discord.SelectOption(label="🚨 Staff Report", value="option_3"),
            discord.SelectOption(label="🔓 Ban Appeal", value="option_4"),
            discord.SelectOption(label="💸 Donation Ticket", value="option_5"),
        ]
        select = discord.ui.Select(placeholder="Make a selection", options=options, custom_id="ticket_dropdown")
        view.add_item(select)
        await interaction.message.edit(view=view)
    
    elif interaction.data["custom_id"] == "helpp_dropdown":
        selected_option = interaction.data["values"][0]
        
        if selected_option == "helpp_option_1":
            title = "Moderation Commands"
            commands_list = ".ban, .banlogs, .boostmessage, .unbanlogs, .kick, .kicklogs, .antiraid, .antiraidwhitelist, .antiraidremove, .antiraidcheck, .level, .resetlevel, .setlevel, setlevelreset, .botwhitelist, .botwhitelistremove, .botwhitelistcheck, .avatarlogs, .noavatarkick, .displaylogs, .memberupdate, .memberupdatestop, .messagelogs, .messagelogstop, .resetrole, .resetvc, .setpanel, .say, .clonesticker/cs, .stealemoji/se, .setrole, .usernamelogs, .setvc, .timeout/to, .untimeout/unto, .timeoutlogs, .vanity, .vanitystop, .welcome, .welcomestop, .autorole, .clear, .nuke, .lock, .unlock, .setprefix, .resetprefix"
        elif selected_option == "helpp_option_2":
            title = "Everyone Commands"
            commands_list = ".hello, .help, .avatar, .info, .prefix, .serverinfo, .vcpanel, .checklevel, .levellb, .setlevelcheck, .members, .reject, .permit, .insta/ig, .roblox/rblx, .inrole, .snipe, .play, .lyrics, .skip, .pause, .resume, .stop (more coming soon)"
        elif selected_option == "helpp_option_3":
            title = "Booster Commands"
            commands_list = ".createvc, .deletevc, .renamevc, .whitelist, .checkwhitelist, .blacklist, .checkblacklist, .disconnect, .lockvc, .unlockvc, .limitvc, .ghostvc, .createrole, .deleterole, .rolecolor, .renamerole"
        else:
            await interaction.response.send_message("Invalid option selected.", ephemeral=True)
            return

        commands = commands_list.split(', ')
        chunks = [commands[i:i + 10] for i in range(0, len(commands), 10)]  # Split commands into chunks of 10

        embed = discord.Embed(title=title)
        for chunk in chunks:
            embed.add_field(name="", value=' '.join(chunk), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    
    elif interaction.data["custom_id"] == "disconnect_dropdown":
        selected_user_id = interaction.data['values'][0]
        voice_channel = interaction.user.voice.channel
        selected_member = voice_channel.guild.get_member(int(selected_user_id))
        if selected_member:
            await selected_member.edit(voice_channel=None)
            await interaction.response.send_message(f"{selected_member.display_name} has been disconnected from {voice_channel.name}.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid user selection.", ephemeral=True)





class ClaimButton(discord.ui.Button):
    def __init__(self, member, staff_role):
        super().__init__(style=discord.ButtonStyle.secondary, label="Claim")
        self.member = member
        self.staff_role = staff_role
        self.claimed_by = None

    async def callback(self, interaction: discord.Interaction):
        global claim_counts

        embed = discord.Embed()
        embed.colour = discord.Colour.dark_gray()

        if self.claimed_by:
            embed.description = f"This ticket has already been claimed by {self.claimed_by.mention}."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if self.staff_role in interaction.user.roles or interaction.user.guild_permissions.administrator:
            # Allow staff or admins to claim the ticket
            self.claimed_by = interaction.user
            overwrites = {
                self.member: discord.PermissionOverwrite(send_messages=True, view_channel=True),
                interaction.user: discord.PermissionOverwrite(send_messages=True, view_channel=True),
                self.staff_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                # Add the specific role with view permission
                interaction.guild.get_role(1388439296813437049): discord.PermissionOverwrite(send_messages=True, view_channel=True)
            }

            # Increment claim count for the user
            user_id = str(interaction.user.id)
            claim_counts[user_id] = claim_counts.get(user_id, 0) + 1

            # Send claim notification to the specified channel
            if claim_notification_channel_id:
                claim_notification_channel = interaction.guild.get_channel(claim_notification_channel_id)
                if claim_notification_channel:
                    channel_name = interaction.channel.name if interaction.channel else "deleted channel"
                    embed.description = f"{interaction.user.mention} has claimed {channel_name} and now has {claim_counts[user_id]} claims."
                    await claim_notification_channel.send(embed=embed)
            else:
                embed.description = "Claim notification channel not set. Please set it using the `claimlogs` command."
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        else:
            # Non-authorized users
            embed.description = "You don't have permission to claim this ticket."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        ticket_channel = interaction.channel
        await ticket_channel.edit(overwrites=overwrites)

        embed.description = f"{interaction.user.mention} has claimed the ticket."
        await interaction.response.send_message(embed=embed, ephemeral=True)




@client.command()
@commands.has_permissions(administrator=True)
async def claimlogs(ctx, channel_id: int):
    global claim_notification_channel_id
    claim_notification_channel_id = channel_id
    embed = discord.Embed(description=f"Claim notification channel set to <#{channel_id}>.")
    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def checkclaims(ctx):
    global claim_counts

    # Filter users with at least one claim
    users_with_claims = {user_id: count for user_id, count in claim_counts.items() if count > 0}

    if not users_with_claims:
        embed = discord.Embed(description="No users have claimed any tickets.")
        await ctx.send(embed=embed)
        return

    # Sort users by claim count
    sorted_users = sorted(users_with_claims.items(), key=lambda x: x[1], reverse=True)

    # Generate pages
    pages = []
    page_content = ""
    for user_id, claim_count in sorted_users:
        user = ctx.guild.get_member(int(user_id))
        if user:
            page_content += f"{user.mention} ({user_id}): **{claim_count} claims\n**"
        else:
            # User not found in the guild
            page_content += f"User ID: {user_id}: {claim_count} claims\n"

        # If page content reaches character limit, start a new page
        if len(page_content) > 1900:  # Discord has a 2000 character limit for messages, leaving a buffer
            pages.append(page_content)
            page_content = ""

    # Add remaining content as the last page
    if page_content:
        pages.append(page_content)

    if not pages:
        embed = discord.Embed(description="No users have claimed any tickets.")
        await ctx.send(embed=embed)
        return

    # Send paginated embeds
    current_page = 0
    embed = discord.Embed(title="Claims Overview", description=pages[current_page])
    embed.set_footer(text=f"Page {current_page + 1}/{len(pages)}")
    message = await ctx.send(embed=embed)

    # Add reactions for pagination if there are multiple pages
    if len(pages) > 1:
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                reaction, user = await client.wait_for("reaction_add", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                break

            if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                current_page += 1
                embed.description = pages[current_page]
                embed.set_footer(text=f"Page {current_page + 1}/{len(pages)}")
                await message.edit(embed=embed)
                await message.remove_reaction(reaction, user)
            elif str(reaction.emoji) == "◀️" and current_page > 0:
                current_page -= 1
                embed.description = pages[current_page]
                embed.set_footer(text=f"Page {current_page + 1}/{len(pages)}")
                await message.edit(embed=embed)
                await message.remove_reaction(reaction, user)

import typing

@client.command()
@commands.has_permissions(administrator=True)
async def resetclaims(ctx, user_id: typing.Optional[int] = None):
    global claim_counts

    if user_id is None:
        # Reset all claims for every user
        claim_counts = {}
        embed = discord.Embed(description="All claim counts have been reset.")
        await ctx.send(embed=embed)
    else:
        # Reset claims for a specific user
        user_id_str = str(user_id)
        if user_id_str in claim_counts:
            del claim_counts[user_id_str]
            embed = discord.Embed(description=f"Claims for user with ID {user_id} have been reset.")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="No claims found for the specified user ID.")
            await ctx.send(embed=embed)

@client.command()
@commands.check(lambda ctx: ctx.author.id == 1074843364480008257)  # Replace YOUR_SPECIFIC_DISCORD_ID with the actual Discord ID
@commands.has_permissions(administrator=True)
async def addclaims(ctx, user_id: int, amount: int):
    global claim_counts

    # Ensure user_id is a string to use as a key in the claim_counts dictionary
    user_id_str = str(user_id)

    # Update claim count for the specified user
    if user_id_str in claim_counts:
        claim_counts[user_id_str] += amount
    else:
        claim_counts[user_id_str] = amount

    embed = discord.Embed(description=f"Added {amount} claim(s) to user with ID {user_id}.")
    await ctx.send(embed=embed)




class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Close")

    async def callback(self, interaction: discord.Interaction):
        # Get ticket information from the channel
        channel = interaction.channel
        messages = [msg async for msg in channel.history(limit=100, oldest_first=True)]
        
        # Find the ticket information from the first embed
        ticket_info = {}
        ticket_type = "Unknown"
        for message in messages:
            if message.embeds:
                embed = message.embeds[0]
                title = embed.title or ""
                if "Robux Purchase Ticket" in title:
                    for field in embed.fields:
                        ticket_info[field.name] = field.value
                    ticket_type = "Robux Purchase"
                elif "Support Ticket" in title:
                    for field in embed.fields:
                        ticket_info[field.name] = field.value
                    ticket_type = "General Support"
                elif "Staff Application" in title:
                    for field in embed.fields:
                        ticket_info[field.name] = field.value
                    ticket_type = "Staff Application"
                elif "Staff Report" in title:
                    for field in embed.fields:
                        ticket_info[field.name] = field.value
                    ticket_type = "Staff Report"
                elif "Ban Appeal" in title:
                    for field in embed.fields:
                        ticket_info[field.name] = field.value
                    ticket_type = "Ban Appeal"
                elif "Donation Ticket" in title:
                    for field in embed.fields:
                        ticket_info[field.name] = field.value
                    ticket_type = "Donation"
                break

        # Get the user who created the ticket (first mentioned user in the channel)
        creator = None
        for message in messages:
            if message.mentions:
                creator = message.mentions[0]
                break

        # Send log to the logs channel
        logs_channel = interaction.guild.get_channel(1396165935085256717)  # Replace with your logs channel ID
        if logs_channel:
            log_embed = discord.Embed(
                title="📝 Ticket Closed",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            log_embed.add_field(name="🎟️ Created By", value=creator.mention if creator else "Unknown", inline=True)
            log_embed.add_field(name="🔒 Closed By", value=interaction.user.mention, inline=True)
            log_embed.add_field(name="📋 Ticket Type", value=ticket_type, inline=True)
            log_embed.add_field(name="📅 Closed At", value=f"<t:{int(datetime.datetime.now().timestamp())}:F>", inline=True)

            # Add ticket-specific fields
            if ticket_type == "Robux Purchase":
                log_embed.add_field(name="💰 Robux Amount", value=ticket_info.get("Robux Amount", "N/A"), inline=True)
                log_embed.add_field(name="💳 Payment Method", value=ticket_info.get("Payment Method", "N/A"), inline=True)
                log_embed.add_field(name="👤 Roblox Username", value=ticket_info.get("Roblox Username", "N/A"), inline=True)
            elif ticket_type == "General Support":
                issue = ticket_info.get("Issue", "N/A")
                if len(issue) > 100:
                    issue = issue[:97] + "..."
                log_embed.add_field(name="❓ Issue", value=issue, inline=False)
                log_embed.add_field(name="🛠️ Attempted Solutions", value=ticket_info.get("Attempted Solutions", "N/A"), inline=False)
            elif ticket_type == "Staff Application":
                log_embed.add_field(name="Why do you want to be staff?", value=ticket_info.get("Why do you want to be staff?", "N/A"), inline=False)
                log_embed.add_field(name="Why are you a good fit?", value=ticket_info.get("Why are you a good fit?", "N/A"), inline=False)
            elif ticket_type == "Staff Report":
                log_embed.add_field(name="Staff User Reported", value=ticket_info.get("Staff User Reported", "N/A"), inline=True)
                log_embed.add_field(name="Reason", value=ticket_info.get("Reason", "N/A"), inline=False)
            elif ticket_type == "Ban Appeal":
                log_embed.add_field(name="Banned User", value=ticket_info.get("Banned User", "N/A"), inline=True)
                log_embed.add_field(name="Why Unban?", value=ticket_info.get("Why Unban?", "N/A"), inline=False)
            elif ticket_type == "Donation":
                log_embed.add_field(name="Donation Amount", value=ticket_info.get("Donation Amount", "N/A"), inline=True)
                log_embed.add_field(name="Reason for Donating", value=ticket_info.get("Reason for Donating", "N/A"), inline=False)

            await logs_channel.send(embed=log_embed)

        # Create an embed to send
        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket will be getting deleted in 5 seconds and got deleted by {interaction.user.mention}",
            color=discord.Color.red()
        )
        
        try:
            # Send the embed message
            await interaction.response.send_message(embed=embed)
            
            # Delete the ticket channel after 5 seconds
            await asyncio.sleep(5)
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to delete the ticket channel.")

class TranscriptButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="Transcript")

    async def callback(self, interaction: discord.Interaction):
        try:
            # Check if the user has the specific role or admin perms
            role_id = 1388439296813437049  # Replace with the specific role ID
            user = interaction.user
            member = interaction.guild.get_member(user.id)
            if role_id not in [role.id for role in member.roles] and not member.guild_permissions.administrator:
                await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
                return
            
            # Inform the user that the transcript is being generated
            await interaction.response.send_message("Transcripting...", ephemeral=True)
            await asyncio.sleep(1)

            # Get the ticket channel where the transcript will be generated
            ticket_channel = interaction.channel

            # Get the specific channel ID where you want to save the transcript
            transcript_channel_id = 1396165935085256717  # Replace with the specific channel ID
            transcript_channel = interaction.guild.get_channel(transcript_channel_id)

            # Ensure the transcript channel exists and is a text channel
            if transcript_channel is None or not isinstance(transcript_channel, discord.TextChannel):
                await interaction.followup.send("Invalid transcript channel configuration.")
                return

            # Fetch recent messages from the ticket channel
            try:
                messages = []
                async for message in ticket_channel.history(limit=None):
                    messages.append((message.author.display_name, message.content))
            except discord.Forbidden:
                await interaction.followup.send("I don't have permission to fetch messages.")
                return

            # Reverse the list of messages to display the oldest message first
            messages.reverse()

            # Generate HTML content for the transcript
            html_content = "<html><head><title>Ticket Transcript</title>"
            html_content += "<style>"
            html_content += "body {font-family: Arial, sans-serif; background-color: #36393F; color: #FFFFFF;}"
            html_content += ".message {margin-bottom: 10px;}"
            html_content += ".message .author {font-weight: bold;}"
            html_content += ".message .content {margin-left: 10px;}"
            html_content += "</style>"
            html_content += "</head><body>"

            for author, content in messages:
                html_content += f'<div class="message"><span class="author">{author}</span><span class="content">{content}</span></div>'

            html_content += "</body></html>"

            # Save the HTML content to a file
            file_name = f"ticket_transcript_{ticket_channel.id}.html"
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(html_content)

            # Send the HTML file as an attachment to the transcript channel
            transcript_file = discord.File(file_name)
            await transcript_channel.send(f"Ticket Transcript generated by {interaction.user.mention}:", file=transcript_file)

            # Delete the temporary HTML file
            os.remove(file_name)

            # Create an embed to send
            embed = discord.Embed(
                title="Transcript Generated",
                description="Transcript has been generated and sent to the transcript channel.",
                color=discord.Color.green()
            )
            
            # Send the embed message along with the text response
            await interaction.followup.send(embed=embed)
        except discord.errors.InteractionResponded:
            pass



@client.command()
async def close(ctx):
    # Define a dictionary mapping category IDs to category names
    ticket_categories = {
        1396165065396322334: "General Support",
        1396165065396322334: "Staff Application",
        1396165065396322334: "Staff Report",
        1396165065396322334: "Ban Appeal",
        1396165065396322334: "Donation Ticket",



        # Add more categories as needed
    }

    # Check if the command is being used in a ticket channel
    channel_category_id = ctx.channel.category_id
    if channel_category_id not in ticket_categories:
        # If the channel category is not a ticket category, inform the user and return
        await ctx.send("This command can only be used within a ticket channel.")
        return

    # Check if the user invoking the command has the necessary permissions
    staff_role_id = 1388439296813437049  # Replace with your staff role ID
    staff_role = ctx.guild.get_role(staff_role_id)
    if not (ctx.author.guild_permissions.administrator or (staff_role and staff_role in ctx.author.roles)):
        await ctx.send("You don't have permission to use this command.")
        return

    # Create an embed to send
    embed = discord.Embed(
        title="Ticket Closed",
        description=f"This ticket will be getting deleted in 5 seconds and got deleted by {ctx.author.mention}",
        color=discord.Color.red()
    )

    try:
        # Send the embed message
        await ctx.send(embed=embed)

        # Delete the ticket channel after 5 seconds
        await asyncio.sleep(5)
        await ctx.channel.delete()
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete the ticket channel.")

@client.command()
async def transcript(ctx):
    # Check if the user invoking the command has the necessary permissions
    staff_role_id = 1388439296813437049  # Replace with your staff role ID
    staff_role = ctx.guild.get_role(staff_role_id)
    if not (ctx.author.guild_permissions.administrator or (staff_role and staff_role in ctx.author.roles)):
        await ctx.send("You don't have permission to use this command.")
        return

    try:
        # Inform the user that the transcript is being generated
        await ctx.send("Transcripting...")

        # Get the ticket channel where the transcript will be generated
        ticket_channel = ctx.channel

        # Get the specific channel ID where you want to save the transcript
        transcript_channel_id = 1396165935085256717  # Replace with the specific channel ID
        transcript_channel = ctx.guild.get_channel(transcript_channel_id)

        # Ensure the transcript channel exists and is a text channel
        if transcript_channel is None or not isinstance(transcript_channel, discord.TextChannel):
            await ctx.send("Invalid transcript channel configuration.")
            return

        # Fetch recent messages from the ticket channel
        try:
            messages = []
            async for message in ticket_channel.history(limit=None):
                messages.append((message.author.display_name, message.content))
        except discord.Forbidden:
            await ctx.send("I don't have permission to fetch messages.")
            return

        # Reverse the list of messages to display the oldest message first
        messages.reverse()

        # Generate HTML content for the transcript
        html_content = "<html><head><title>Ticket Transcript</title>"
        html_content += "<style>"
        html_content += "body {font-family: Arial, sans-serif; background-color: #36393F; color: #FFFFFF;}"
        html_content += ".message {margin-bottom: 10px;}"
        html_content += ".message .author {font-weight: bold;}"
        html_content += ".message .content {margin-left: 10px;}"
        html_content += "</style>"
        html_content += "</head><body>"

        for author, content in messages:
            html_content += f'<div class="message"><span class="author">{author}</span><span class="content">{content}</span></div>'

        html_content += "</body></html>"

        # Save the HTML content to a file
        file_name = f"ticket_transcript_{ticket_channel.id}.html"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(html_content)

        # Send the HTML file as an attachment to the transcript channel
        transcript_file = discord.File(file_name)
        await transcript_channel.send(f"Ticket Transcript generated by {ctx.author.mention}:", file=transcript_file)

        # Delete the temporary HTML file
        os.remove(file_name)

        # Create an embed to send
        embed = discord.Embed(
            title="Transcript Generated",
            description="Transcript has been generated and sent to the transcript channel.",
            color=discord.Color.green()
        )

        # Send the embed message along with the text response
        await ctx.send(embed=embed)
    except discord.errors.InteractionResponded:
        pass



@client.command()
async def add(ctx, target):
    # Check if the user invoking the command has the staff role or admin perms
    staff_role_id = 1388439296813437049  # Replace with your staff role ID
    staff_role = ctx.guild.get_role(staff_role_id)
    if not (ctx.author.guild_permissions.administrator or (staff_role and staff_role in ctx.author.roles)):
        embed = discord.Embed(
            title="Permission Denied",
            description="You don't have permission to use this command.",
            color=0x2a2d30  # Set color to 0x2a2d30
        )
        await ctx.send(embed=embed)
        return

    # Get the ticket channel
    ticket_channel = ctx.channel

    # Check if the target is a role mention
    if target.startswith("<@&") and target.endswith(">"):
        role_id = int(target[3:-1])
        role = ctx.guild.get_role(role_id)
        if role:
            # Add the role to the ticket channel
            await ticket_channel.set_permissions(role, view_channel=True, send_messages=True)
            embed = discord.Embed(
                title="Role Added",
                description=f"{role.name} has been added to the ticket.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Role Not Found",
                description="The specified role was not found.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)
    else:
        # Try to convert target to a discord.Member object
        try:
            user = await commands.MemberConverter().convert(ctx, target)
        except commands.MemberNotFound:
            # If the conversion fails, try to find the user by name
            user = discord.utils.find(lambda m: m.name == target or str(m) == target, ctx.guild.members)

        if user:
            # Add the user to the ticket channel
            await ticket_channel.set_permissions(user, view_channel=True, send_messages=True)
            embed = discord.Embed(
                title="User Added",
                description=f"{user.mention} has been added to the ticket.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="User Not Found",
                description="The specified user was not found.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)

@client.command()
async def remove(ctx, target):
    # Check if the user invoking the command has the staff role or admin perms
    staff_role_id = 1388439296813437049  # Replace with your staff role ID
    staff_role = ctx.guild.get_role(staff_role_id)
    if not (ctx.author.guild_permissions.administrator or (staff_role and staff_role in ctx.author.roles)):
        embed = discord.Embed(
            title="Permission Denied",
            description="You don't have permission to use this command.",
            color=0x2a2d30  # Set color to 0x2a2d30
        )
        await ctx.send(embed=embed)
        return

    # Get the ticket channel
    ticket_channel = ctx.channel

    # Check if the target is a role mention
    if target.startswith("<@&") and target.endswith(">"):
        role_id = int(target[3:-1])
        role = ctx.guild.get_role(role_id)
        if role:
            # Remove the role from the ticket channel
            await ticket_channel.set_permissions(role, read_messages=False, send_messages=False)
            embed = discord.Embed(
                title="Role Removed",
                description=f"{role.name} has been removed from the ticket.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Role Not Found",
                description="The specified role was not found.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)
    else:
        # Try to convert target to a discord.Member object
        try:
            user = await commands.MemberConverter().convert(ctx, target)
        except commands.MemberNotFound:
            # If the conversion fails, try to find the user by name
            user = discord.utils.find(lambda m: m.name == target or str(m) == target, ctx.guild.members)

        if user:
            # Remove the user from the ticket channel
            await ticket_channel.set_permissions(user, read_messages=False, send_messages=False)
            embed = discord.Embed(
                title="User Removed",
                description=f"{user.mention} has been removed from the ticket.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="User Not Found",
                description="The specified user was not found.",
                color=0x2a2d30  # Set color to 0x2a2d30
            )
            await ctx.send(embed=embed)


@client.command()
async def rename(ctx, *, new_name):
    # Check if the user invoking the command has the staff role or admin perms
    staff_role_id = 1388439296813437049  # Replace with your staff role ID
    staff_role = ctx.guild.get_role(staff_role_id)
    if not (ctx.author.guild_permissions.administrator or (staff_role and staff_role in ctx.author.roles)):
        embed = discord.Embed(description="You don't have permission to use this command.", color=0x2a2d30)  # Set color to 0x2a2d30
        await ctx.send(embed=embed)
        return
    
    # Get the ticket channel
    ticket_channel = ctx.channel
    
    # Rename the ticket channel
    try:
        await ticket_channel.edit(name=new_name)
        embed = discord.Embed(description=f"Ticket has been renamed to `{new_name}`.", color=0x2a2d30)  # Set color to 0x2a2d30
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(description="I don't have permission to rename the ticket.", color=0x2a2d30)  # Set color to 0x2a2d30
        await ctx.send(embed=embed)

roster = {
    "Server Management": [],
    "Head Management": [],
    "Senior Management": [],
    "Management": [],
    "Community Manager": [],
    "Head of Staff": [],
    "Head Administrator": [],
    "Senior Administrator": [],
    "Administrator": [],
    "Head Moderator": [],
    "Senior Moderator": [],
    "Moderator": [],
    "Trial Moderator": [],
    "Support": []
}




