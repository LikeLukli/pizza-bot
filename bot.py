import os
import discord
import asyncio

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

from services.logger_conf import BotLogger
from services.storage import init_db

# configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class PizzaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.order_cog")

        await self.tree.sync()


bot_logger = BotLogger(log_dir="data/logs/").bot_logger

# Load secrets from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = PizzaBot()

@bot.event
async def on_ready():
    init_db()
    bot_logger.info(f'We have logged in as {bot.user}.')

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
