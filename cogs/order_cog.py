import discord
from discord import app_commands
from discord.ext import commands

from services import order_service


def requires_setup():
    """Check if the guild has been set up."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Dieser Befehl funktioniert nur in einem Server.", ephemeral=True
            )
            return False

        if not order_service.is_guild_setup(interaction.guild_id):
            await interaction.response.send_message(
                "❌ Der Bot wurde noch nicht eingerichtet. Ein Admin muss `/setup` ausführen.",
                ephemeral=True
            )
            return False

        return True

    return app_commands.check(predicate)


class OrderCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Autocomplete: show existing menu items
    # ------------------------------------------------------------------
    async def item_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        items = order_service.get_menu_items()
        return [
            app_commands.Choice(name=f"{i['name']} (€{i['price']:.2f})", value=i['name'])
            for i in items
            if current.lower() in i['name'].lower()
        ][:25]

    # ------------------------------------------------------------------
    # /order
    # ------------------------------------------------------------------
    @app_commands.command(name="order", description="Füge ein Item zu deiner aktuellen Bestellung hinzu")
    @app_commands.describe(
        item="Was möchtest du bestellen?",
        quantity="Wie viele? (Standard: 1)",
        extra_wishes="Besondere Wünsche (optional)",
    )
    @app_commands.autocomplete(item=item_autocomplete)
    @requires_setup()
    async def order(
        self,
        interaction: discord.Interaction,
        item: str,
        quantity: app_commands.Range[int, 1] = 1,
        extra_wishes: str = None,
    ):
        # Look up the price from the menu
        menu = order_service.get_menu_items()
        menu_item = next((i for i in menu if i["name"].lower() == item.lower()), None)

        if menu_item is None:
            await interaction.response.send_message(
                f"❌ **{item}** ist nicht im Menü. Bitte wähle ein Item aus der Liste.",
                ephemeral=True,
            )
            return

        user = interaction.user
        result = order_service.add_item(
            user_id=user.id,
            username=user.name,
            avatar_url=str(user.display_avatar.url),
            item_name=menu_item["name"],
            item_price=menu_item["price"],
            quantity=quantity,
            extra_wishes=extra_wishes,
        )

        desc = f"**{quantity}x {menu_item['name']}** (€{menu_item['price']:.2f})"
        if extra_wishes:
            desc += f"\n📝 _{extra_wishes}_"

        embed = discord.Embed(
            title="✅ Bestellung aufgenommen",
            description=desc,
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Bestellung #{result['order_id']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /myorder
    # ------------------------------------------------------------------
    @app_commands.command(name="myorder", description="Zeige deine aktuelle offene Bestellung")
    @requires_setup()
    async def myorder(self, interaction: discord.Interaction):
        order = order_service.get_current_order(interaction.user.id)

        if order is None:
            await interaction.response.send_message(
                "Du hast aktuell keine offene Bestellung.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🛒 Deine Bestellung #{order['id']}",
            color=discord.Color.blurple(),
        )

        total = 0.0
        for i in order["items"]:
            subtotal = i["price"] * i["quantity"]
            total += subtotal
            value = f"€{i['price']:.2f} x {i['quantity']} = **€{subtotal:.2f}**"
            if i["extra_wishes"]:
                value += f"\n📝 _{i['extra_wishes']}_"
            embed.add_field(name=i["name"], value=value, inline=False)

        embed.set_footer(text=f"Gesamt: €{total:.2f}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /removeitem
    # ------------------------------------------------------------------
    @app_commands.command(name="removeitem", description="Entferne ein Item aus deiner aktuellen Bestellung")
    @app_commands.describe(item="Name des Items, das du entfernen möchtest")
    @app_commands.autocomplete(item=item_autocomplete)
    @requires_setup()
    async def removeitem(self, interaction: discord.Interaction, item: str):
        success = order_service.remove_item(interaction.user.id, item)

        if success:
            await interaction.response.send_message(
                f"🗑️ **{item}** wurde aus deiner Bestellung entfernt.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ **{item}** wurde nicht in deiner Bestellung gefunden.", ephemeral=True
            )

    # ------------------------------------------------------------------
    # Error handler for this cog
    # ------------------------------------------------------------------
    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.TransformerError):
            await interaction.response.send_message(
                f"❌ Ungültige Eingabe: **{error.value}**\n"
                "Bitte wähle einen Wert aus der Dropdown-Liste aus.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.CheckFailure):
            # Already handled by the check itself
            pass
        else:
            await interaction.response.send_message(
                f"❌ Ein Fehler ist aufgetreten: {error}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(OrderCog(bot))