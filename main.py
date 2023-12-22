import discord
from discord.ext import commands
from gov.commands import setup_gov_commands
from gov.events import setup_gov_events
from constants import DISCORD_BOT_TOKEN

def main():

    # Discord Config
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    bot = commands.Bot(command_prefix="$", intents=intents)
    
    # Setup the governance discord commands, and events
    setup_gov_commands(bot)
    setup_gov_events(bot)

    # Run the bot
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()