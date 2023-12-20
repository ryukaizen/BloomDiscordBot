import discord
from discord.ext import commands
from emotes.commands import setup_contrbitutor_commands
from emotes.events import setup_contributor_events
from constants import DISCORD_BOT_TOKEN, FILE_PATH
import json

def main():
    # Load contributors and emoji ID mapping from contributors.json
    with open(FILE_PATH, 'r') as json_file:
        data = json.load(json_file)
        contributors = data["contributors"]
        emoji_id_mapping = {emoji: contributor for emoji, contributor in data["emojiIdMapping"].items()}

    # Discord Config
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    bot = commands.Bot(command_prefix="$", intents=intents)
    
    # Setup the emotes discord commands, and events
    setup_contrbitutor_commands(bot, contributors, emoji_id_mapping)
    setup_contributor_events(bot, contributors, emoji_id_mapping)

    # Run the bot
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()