import discord
from discord import app_commands
from discord.ext import commands

from services import order_service


def is_manager():
    """
    Check if user can manage orders:
    - Server owner can always manage
    - Users with the configured manager role can manage
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Dieser Befehl funktioniert nur in einem Server.", ephemeral=True
            )
            return False

        # Check if guild is set up
        if not order_service.is_guild_setup(interaction.guild_id):
            await interaction.response.send_message(
                "❌ Der Bot wurde noch nicht eingerichtet. Ein Admin muss `/setup` ausführen.",
                ephemeral=True
            )
            return False

        # Server owner can always manage
        if interaction.user.id == interaction.guild.owner_id:
            return True

        # Check for manager role
        manager_role_id = order_service.get_manager_role(interaction.guild_id)
        if manager_role_id:
            member = interaction.user
            if any(role.id == manager_role_id for role in member.roles):
                return True

        await interaction.response.send_message(
            "❌ Du brauchst die Besteller-Rolle für diesen Befehl.", ephemeral=True
        )
        return False

    return app_commands.check(predicate)


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


class MenuPaginationView(discord.ui.View):
    """Pagination view for /menu command"""

    ITEMS_PER_PAGE = 10

    def __init__(self, items: list[dict], user_id: int):
        super().__init__(timeout=300)
        self.items = items
        self.user_id = user_id
        self.current_page = 0
        self.total_pages = max(1, (len(items) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.update_buttons()

    def get_page_content(self) -> str:
        """Get the content for the current page"""
        start = self.current_page * self.ITEMS_PER_PAGE
        end = start + self.ITEMS_PER_PAGE
        page_items = self.items[start:end]

        lines = []
        for item in page_items:
            line = f"• **{item['name']}** {item['price']:.2f}€"
            if item.get("description"):
                line += f" | _{item['description']}_"
            lines.append(line)

        return "\n".join(lines) if lines else "Keine Items"

    def update_buttons(self):
        """Update button states based on current page"""
        self.prev_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to interact"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Nur der ursprüngliche Nutzer kann diese Buttons verwenden.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="◀ Zurück", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        embed = discord.Embed(
            title="🍕 Menü",
            description=self.get_page_content(),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Seite {self.current_page + 1}/{self.total_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Weiter ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        embed = discord.Embed(
            title="🍕 Menü",
            description=self.get_page_content(),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Seite {self.current_page + 1}/{self.total_pages}")
        await interaction.response.edit_message(embed=embed, view=self)


class ClosedOrdersPaginationView(discord.ui.View):
    """Pagination view for closed orders in /stats"""

    ITEMS_PER_PAGE = 10

    def __init__(self, items: list[dict], user_id: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.items = items
        self.user_id = user_id
        self.current_page = 0
        self.total_pages = max(1, (len(items) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.update_buttons()

    def get_page_content(self) -> str:
        """Get the content for the current page"""
        start = self.current_page * self.ITEMS_PER_PAGE
        end = start + self.ITEMS_PER_PAGE
        page_items = self.items[start:end]

        if not page_items:
            return "Keine abgeschlossenen Bestellungen"

        return "\n".join(
            f"• {item['quantity']}x {item['name']}"
            for item in page_items
        )

    def update_buttons(self):
        """Update button states based on current page"""
        self.prev_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    async def rebuild_embed(self, interaction: discord.Interaction):
        """Rebuild the stats embed with updated page"""
        stats = order_service.get_stats()

        embed = discord.Embed(
            title="📊 Bestellstatistiken",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="📦 Bestellungen gesamt",
            value=str(stats["total_orders"]),
            inline=True
        )
        embed.add_field(
            name="📅 Bestellungen heute",
            value=str(stats["orders_today"]),
            inline=True
        )
        embed.add_field(
            name="👥 Nutzer gesamt",
            value=str(stats["total_users"]),
            inline=True
        )
        embed.add_field(
            name="💰 Umsatz (abgeschlossen)",
            value=f"€{stats['total_revenue']:.2f}",
            inline=True
        )

        status_text = "\n".join(
            f"• {status}: {count}"
            for status, count in stats["orders_by_status"].items()
        ) or "Keine Bestellungen"
        embed.add_field(
            name="📋 Nach Status",
            value=status_text,
            inline=True
        )

        if stats["popular_items"]:
            popular_text = "\n".join(
                f"• {item['name']}: {item['quantity']}x"
                for item in stats["popular_items"]
            )
            embed.add_field(
                name="🏆 Beliebteste Items",
                value=popular_text,
                inline=False
            )

        embed.add_field(
            name="✅ Abgeschlossene Bestellungen",
            value=self.get_page_content(),
            inline=False
        )
        embed.set_footer(text=f"Seite {self.current_page + 1}/{self.total_pages}")

        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to interact"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Nur der ursprüngliche Nutzer kann diese Buttons verwenden.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="◀ Zurück", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        embed = await self.rebuild_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Weiter ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        embed = await self.rebuild_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # /setup — only server owner or Discord admin can run this
    # ------------------------------------------------------------------
    @app_commands.command(
        name="setup",
        description="Richte den Bot ein: Wähle Kanal und Besteller-Rolle"
    )
    @app_commands.describe(
        channel="Der Kanal für Bestellbenachrichtigungen",
        manager_role="Die Rolle, die Bestellungen verwalten darf"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        manager_role: discord.Role
    ):
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Dieser Befehl funktioniert nur in einem Server.", ephemeral=True
            )
            return

        order_service.setup_guild(
            guild_id=interaction.guild_id,
            channel_id=channel.id,
            role_id=manager_role.id
        )

        embed = discord.Embed(
            title="✅ Bot eingerichtet!",
            color=discord.Color.green(),
        )
        embed.add_field(name="📢 Bestellkanal", value=channel.mention, inline=True)
        embed.add_field(name="👥 Besteller-Rolle", value=manager_role.mention, inline=True)
        embed.set_footer(text="Nutzer mit der Besteller-Rolle können jetzt Bestellungen verwalten.")

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /additem
    # ------------------------------------------------------------------
    @app_commands.command(name="additem", description="Füge ein neues Item zum Menü hinzu")
    @app_commands.describe(
        name="Name des Items",
        price="Preis in € (z.B. 8.50)",
        description="Beschreibung des Items (optional)"
    )
    @is_manager()
    async def additem(
        self,
        interaction: discord.Interaction,
        name: str,
        price: float,
        description: str = None
    ):
        try:
            item = order_service.create_menu_item(name, price, description)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Item hinzugefügt",
            color=discord.Color.green(),
        )
        embed.add_field(name="Name", value=item['name'], inline=True)
        embed.add_field(name="Preis", value=f"€{item['price']:.2f}", inline=True)
        if item['description']:
            embed.add_field(name="Beschreibung", value=item['description'], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /orders — show all open orders
    # ------------------------------------------------------------------
    @app_commands.command(name="orders", description="Zeige alle offenen Bestellungen")
    @is_manager()
    async def orders(self, interaction: discord.Interaction):
        open_orders = order_service.get_all_open_orders()

        if not open_orders:
            await interaction.response.send_message(
                "📭 Keine offenen Bestellungen.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🛒 Offene Bestellungen",
            color=discord.Color.orange(),
        )

        for order in open_orders:
            lines = []
            total = 0.0
            for item in order["items"]:
                subtotal = item["price"] * item["quantity"]
                total += subtotal
                line = f"• {item['quantity']}x **{item['name']}** = €{subtotal:.2f}"
                if item["extra_wishes"]:
                    line += f" _({item['extra_wishes']})_"
                lines.append(line)
            lines.append(f"**Gesamt: €{total:.2f}**")

            embed.add_field(
                name=f"#{order['id']} — {order['username']}",
                value="\n".join(lines) or "—",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /markdone — close all open orders and notify users
    # ------------------------------------------------------------------
    @app_commands.command(
        name="markdone",
        description="Markiere alle offenen Bestellungen als bestellt und benachrichtige die User"
    )
    @is_manager()
    async def markdone(self, interaction: discord.Interaction):
        open_orders = order_service.get_all_open_orders()

        if not open_orders:
            await interaction.response.send_message(
                "📭 Keine offenen Bestellungen zum Abschließen.", ephemeral=True
            )
            return

        affected_user_ids = [o["user_id"] for o in open_orders]
        order_service.close_daily_orders()

        mentions = " ".join(f"<@{uid}>" for uid in affected_user_ids)
        channel_id = order_service.get_order_channel(interaction.guild_id)
        channel = self.bot.get_channel(channel_id) if channel_id else interaction.channel

        await interaction.response.send_message(
            "✅ Alle Bestellungen wurden als bestellt markiert.", ephemeral=True
        )
        await channel.send(
            f"🍕 **Bestellung aufgegeben!**\n{mentions}\nEure Bestellungen wurden abgeschickt. Guten Appetit!"
        )

    # ------------------------------------------------------------------
    # /cancelorders — cancel all open orders and notify users
    # ------------------------------------------------------------------
    @app_commands.command(
        name="cancelorders",
        description="Breche alle offenen Bestellungen ab und benachrichtige die User"
    )
    @is_manager()
    async def cancelorders(self, interaction: discord.Interaction):
        affected_user_ids = order_service.cancel_daily_orders()

        if not affected_user_ids:
            await interaction.response.send_message(
                "📭 Keine offenen Bestellungen zum Abbrechen.", ephemeral=True
            )
            return

        mentions = " ".join(f"<@{uid}>" for uid in affected_user_ids)
        channel_id = order_service.get_order_channel(interaction.guild_id)
        channel = self.bot.get_channel(channel_id) if channel_id else interaction.channel

        await interaction.response.send_message(
            "✅ Alle Bestellungen wurden abgebrochen.", ephemeral=True
        )
        await channel.send(
            f"❌ **Bestellung abgebrochen!**\n{mentions}\nLeider wurden eure Bestellungen abgebrochen."
        )

    # ------------------------------------------------------------------
    # /menu — show all available menu items
    # ------------------------------------------------------------------
    @app_commands.command(name="menu", description="Zeige alle verfügbaren Items im Menü")
    @requires_setup()
    async def menu(self, interaction: discord.Interaction):
        items = order_service.get_menu_items()

        if not items:
            await interaction.response.send_message(
                "📭 Das Menü ist noch leer. Ein Besteller muss Items mit `/additem` hinzufügen.",
                ephemeral=True
            )
            return

        view = MenuPaginationView(items, interaction.user.id)
        embed = discord.Embed(
            title="🍕 Menü",
            description=view.get_page_content(),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Seite {view.current_page + 1}/{view.total_pages}")

        await interaction.response.send_message(embed=embed, view=view)

    # ------------------------------------------------------------------
    # Autocomplete: show existing menu items for deletion
    # ------------------------------------------------------------------
    async def menu_item_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        items = order_service.get_menu_items()
        return [
            app_commands.Choice(name=f"{i['name']} (€{i['price']:.2f})", value=i['name'])
            for i in items
            if current.lower() in i['name'].lower()
        ][:25]

    # ------------------------------------------------------------------
    # /deleteitem — remove an item from the menu
    # ------------------------------------------------------------------
    @app_commands.command(name="deleteitem", description="Entferne ein Item aus dem Menü")
    @app_commands.describe(item="Name des Items, das du entfernen möchtest")
    @app_commands.autocomplete(item=menu_item_autocomplete)
    @is_manager()
    async def deleteitem(self, interaction: discord.Interaction, item: str):
        success = order_service.delete_menu_item(item)

        if success:
            await interaction.response.send_message(
                f"✅ **{item}** wurde aus dem Menü entfernt.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ **{item}** wurde nicht im Menü gefunden.", ephemeral=True
            )

    # ------------------------------------------------------------------
    # /stats — show order statistics with pagination for closed orders
    # ------------------------------------------------------------------
    @app_commands.command(name="stats", description="Zeige Bestellstatistiken")
    @is_manager()
    async def stats(self, interaction: discord.Interaction):
        stats = order_service.get_stats()

        embed = discord.Embed(
            title="📊 Bestellstatistiken",
            color=discord.Color.blue(),
        )

        # General stats
        embed.add_field(
            name="📦 Bestellungen gesamt",
            value=str(stats["total_orders"]),
            inline=True
        )
        embed.add_field(
            name="📅 Bestellungen heute",
            value=str(stats["orders_today"]),
            inline=True
        )
        embed.add_field(
            name="👥 Nutzer gesamt",
            value=str(stats["total_users"]),
            inline=True
        )

        # Revenue
        embed.add_field(
            name="💰 Umsatz (abgeschlossen)",
            value=f"€{stats['total_revenue']:.2f}",
            inline=True
        )

        # Orders by status
        status_text = "\n".join(
            f"• {status}: {count}"
            for status, count in stats["orders_by_status"].items()
        ) or "Keine Bestellungen"
        embed.add_field(
            name="📋 Nach Status",
            value=status_text,
            inline=True
        )

        # Most popular items
        if stats["popular_items"]:
            popular_text = "\n".join(
                f"• {item['name']}: {item['quantity']}x"
                for item in stats["popular_items"]
            )
            embed.add_field(
                name="🏆 Beliebteste Items",
                value=popular_text,
                inline=False
            )

        # Closed orders - paginated
        closed_items = stats["closed_items"]
        if closed_items:
            view = ClosedOrdersPaginationView(closed_items, interaction.user.id)
            embed.add_field(
                name="✅ Abgeschlossene Bestellungen",
                value=view.get_page_content(),
                inline=False
            )
            embed.set_footer(text=f"Seite {view.current_page + 1}/{view.total_pages}")
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            embed.add_field(
                name="✅ Abgeschlossene Bestellungen",
                value="Keine abgeschlossenen Bestellungen",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

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
    await bot.add_cog(AdminCog(bot))
