import os
import discord

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

from services.logger_conf import BotLogger

bot_logger = BotLogger(log_dir="data/logs/").bot_logger

# Load secrets from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    bot_logger.info(f'We have logged in as {client.user}.')

# start bot and add handler
client.run(TOKEN)