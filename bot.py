import os
import logging
import discord

from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# logging paths
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# bot logger & discord logger
bot_logger = logging.getLogger("pizza_bot")
bot_logger.setLevel(logging.DEBUG)

discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.INFO)

# file handler
file_handler = logging.FileHandler(filename=LOG_DIR / "bot.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

discord_file_handler = logging.FileHandler(filename=LOG_DIR / "discord.log", encoding="utf-8")
discord_file_handler.setLevel(logging.INFO)

# console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

discord_console_handler = logging.StreamHandler()
discord_console_handler.setLevel(logging.INFO)

# formatting
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

discord_file_handler.setFormatter(formatter)
discord_console_handler.setFormatter(formatter)

# add both handlers to the logger
bot_logger.addHandler(file_handler)
bot_logger.addHandler(console_handler)

discord_logger.addHandler(discord_file_handler)
discord_logger.addHandler(discord_console_handler)

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