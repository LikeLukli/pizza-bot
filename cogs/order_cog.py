import discord

from discord import app_commands
from discord.ext import commands

class OrderCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="order", description="Bestelle etwas")
    async def order(self, interaction: discord.Interaction):
        await interaction.response.send_message("Deine Bestellung wurde aufgenommen!")

async def setup(bot: commands.Bot):
    await bot.add_cog(OrderCog(bot))