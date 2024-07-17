import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import db as database

# Load environment variables from .env file
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

# Initialize the database
database.init_db()

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command(name='gamble')
async def gamble(ctx, amount: int, multiplier: int, win: str = None):
    user = ctx.author

    if win not in ['win', 'lose']:
        await ctx.send('You must specify if you will win or lose. Usage: $gamble <amount> <multiplier> <win|lose>')
        return

    win = win == 'win'

    if amount <= 0 or multiplier <= 0:
        await ctx.send('Amount and multiplier must be positive integers. Usage: $gamble <amount> <multiplier> <win|lose>')
        return

    current_balance = database.get_balance(user.id)

    if current_balance < amount:
        await ctx.send('You do not have enough balance to gamble this amount.')
        return

    # Check for existing pending gamble
    pending_gamble = database.get_pending_gamble(user.id)
    if pending_gamble:
        await ctx.send('You already have a pending gamble. Please resolve it before starting a new one.')
        return

    database.store_pending_gamble(user.id, amount, multiplier, win)
    await ctx.send(f'Accumulator is on for {amount * multiplier} squids! Run $payout if it was a win or loss.')

@bot.command(name='payout')
async def payout(ctx, win: str = None):
    user = ctx.author

    if win not in ['win', 'lose']:
        await ctx.send('You must specify if the result was win or lose. Usage: $payout <win|lose>')
        return

    win = win == 'win'
    pending_gamble = database.get_pending_gamble(user.id)

    if not pending_gamble:
        await ctx.send('You have no pending gambles.')
        return

    amount, multiplier, win_selected = pending_gamble
    amount_won = amount * multiplier if win_selected == win else 0
    amount_lost = amount * multiplier if win_selected != win else 0

    if win_selected == win:
        database.update_balance(user.id, amount_won)
        await ctx.send(f'Congratulations! You won {amount_won} squids!')
    else:
        database.update_balance(user.id, -amount_lost)
        await ctx.send(f'Sorry, you lost {amount_lost} squids.')

    database.update_gamble_stats(user.id, win_selected == win, win_selected, amount_won, amount_lost)
    database.clear_pending_gamble(user.id)

@bot.command(name='cancel')
async def cancel(ctx):
    user = ctx.author
    pending_gamble = database.get_pending_gamble(user.id)

    if not pending_gamble:
        await ctx.send('You have no pending gambles to cancel.')
        return

    database.clear_pending_gamble(user.id)
    await ctx.send('Your pending gamble has been canceled.')

@bot.command(name='sell')
async def sell(ctx, item: str = None):
    user = ctx.author

    if not item:
        await ctx.send('You need to specify the item you want to sell. Usage: $sell <item>')
        return

    if database.has_sold_item(user.id, item):
        await ctx.send(f'You have already sold the {item}. You cannot sell it again.')
        return

    total_sale = random.randint(1, 500)
    database.update_balance(user.id, total_sale)
    database.add_sold_item(user.id, item)
    database.update_gamble_stats(user.id, False, False, 0, 0, item_sold=True)
    new_balance = database.get_balance(user.id)

    await ctx.send(f'You sold your {item} for {total_sale} squids. Your new balance is {new_balance} squids.')

@bot.command(name='stats')
async def stats(ctx):
    user = ctx.author
    wins, losses, bets_won, amount_won, amount_lost, items_sold = database.get_gamble_stats(user.id)
    await ctx.send(
        f'```Stats for {user.name}:\n'
        f'Wins: {wins}\n'
        f'Losses: {losses}\n'
        f'Bets on Win: {bets_won}\n'
        f'Amount Won: {amount_won} squids\n'
        f'Amount Lost: {amount_lost} squids\n'
        f'Items Sold: {items_sold}```'
    )

@bot.command(name='leaderboard')
async def leaderboard(ctx, stat: str = 'bets_won'):
    valid_stats = ['wins', 'losses', 'bets_won', 'amount_won', 'amount_lost', 'items_sold']
    if stat not in valid_stats:
        await ctx.send(f'Invalid stat. Choose from: {", ".join(valid_stats)}')
        return

    leaderboard = database.get_leaderboard(stat)
    if not leaderboard:
        await ctx.send('No data available for the leaderboard.')
        return

    leaderboard_message = f'Leaderboard for {stat}:\n'
    for rank, (user_id, value) in enumerate(leaderboard, start=1):
        user = await bot.fetch_user(user_id)
        leaderboard_message += f'{rank}. {user.name} - {value}\n'

    await ctx.send(leaderboard_message)

@bot.command(name='balance')
async def balance(ctx):
    user = ctx.author
    current_balance = database.get_balance(user.id)
    await ctx.send(f'{user.name}, your current balance is {current_balance} squids.')

@bot.command(name='info')
async def help_command(ctx):
    help_message = (
        "```"
        "**Available Commands:**\n\n"
        "$gamble <amount> <multiplier> <win|lose> - Gamble an amount with a multiplier. Specify if you will win or lose.\n"
        "  Example: $gamble 10 2 win\n\n"
        "$payout <win|lose> - Payout the result of your pending gamble.\n"
        "  Example: $payout win\n\n"
        "$cancel - Cancel your pending gamble.\n"
        "  Example: $cancel\n\n"
        "$sell <item> - Sell an item for random amount of squids.\n"
        "  Example: $sell fish\n\n"
        "$stats - Display your gambling statistics.\n\n"
        "$leaderboard <stat> - Display the leaderboard for a specific stat (wins, losses, bets_won, amount_won, amount_lost, items_sold (default = bets_won)).\n\n"
        "$balance - Display your current balance.\n\n"
        "$info - Display this help message.\n"
        "```"
    )
    await ctx.send(help_message)

# Start the bot with the token from the environment variable
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
