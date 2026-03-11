import os
import discord
import asyncio

from dotenv import load_dotenv
from discord.ext import commands

from services.logger_conf import BotLogger
from services.storage import init_db

# configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Load secrets from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEV_GUILD_ID = os.getenv('DISCORD_GUILD_ID')


class PizzaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # DB should be ready before cogs use storage/services.
        init_db()

        await self.load_extension("cogs.order_cog")
        await self.load_extension("cogs.admin_cog")

        # Sync globally (takes up to 1h to propagate to all guilds)
        global_synced = await self.tree.sync()
        bot_logger.info(f"Synced {len(global_synced)} global commands.")

        # If dev guild is set, clear any guild-specific commands there
        # so only global commands are visible (no duplicates)
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)
            bot_logger.info(f"Cleared guild-specific commands from dev guild {DEV_GUILD_ID}.")


bot_logger = BotLogger(log_dir="data/logs/").bot_logger

bot = PizzaBot()


@bot.event
async def on_ready():
    bot_logger.info(f"We have logged in as {bot.user}.")


async def main():
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
