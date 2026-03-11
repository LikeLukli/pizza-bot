import sqlite3
import os
from pathlib import Path

_connection = None
_filename = None

def get_connection():
    global _connection, _filename
    if _connection is None:
        _connection = sqlite3.connect(_filename)
        _connection.row_factory = sqlite3.Row

    return _connection


def init_db(filename="./data/db/orders.db"):
    global _filename
    _filename = filename

    path_without_file = Path(filename).parent
    if not os.path.exists(path_without_file):
        os.makedirs(path_without_file)

    # sqlite3.connect() creates the file automatically, no need to create it manually

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        avatar_url TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'open',
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        extra_wishes TEXT,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (item_id) REFERENCES items(item_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_config (
        guild_id INTEGER PRIMARY KEY,
        order_channel_id INTEGER,
        manager_role_id INTEGER
    )
    """)

    # Migration: Add manager_role_id column if it doesn't exist (for existing DBs)
    cursor.execute("PRAGMA table_info(guild_config)")
    columns = [row[1] for row in cursor.fetchall()]
    if "manager_role_id" not in columns:
        cursor.execute("ALTER TABLE guild_config ADD COLUMN manager_role_id INTEGER")

    # Migration: Add description column to items if it doesn't exist
    cursor.execute("PRAGMA table_info(items)")
    columns = [row[1] for row in cursor.fetchall()]
    if "description" not in columns:
        cursor.execute("ALTER TABLE items ADD COLUMN description TEXT")

    connection.commit()


def close_db():
    connection = get_connection()
    connection.close()

def get_open_orders() -> list:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM orders WHERE status='open'")
    return cursor.fetchall()

#TODO
def get_or_create_user(user_id: int, username: str, avatar_url: str) -> dict:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user:
        return dict(user)

    cursor.execute("INSERT INTO users (user_id, username, avatar_url) VALUES (?, ?, ?)", (user_id, username, avatar_url))
    connection.commit()

    return {"user_id": user_id, "username": username, "avatar_url": avatar_url}


def get_user_open_order(user_id: int) -> dict | None:
    """Returns the user's currently open order, or None if there isn't one."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE user_id=? AND status='open'",
        (user_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def create_order(user_id: int) -> int:
    """Creates a new open order for the user and returns the new order id."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, status) VALUES (?, 'open')",
        (user_id,)
    )
    connection.commit()
    return cursor.lastrowid


def add_item_to_order(order_id: int, item_id: int, quantity: int, extra_wishes: str = None) -> bool:
    """
    Adds an item to an order.
    If the same item (with the same extra_wishes) already exists in the order,
    the quantity is incremented instead of inserting a duplicate row.
    Returns True on success.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, quantity FROM order_items
        WHERE order_id=? AND item_id=? AND (extra_wishes IS ? OR extra_wishes=?)
        """,
        (order_id, item_id, extra_wishes, extra_wishes)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE order_items SET quantity=? WHERE id=?",
            (existing["quantity"] + quantity, existing["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO order_items (order_id, item_id, quantity, extra_wishes) VALUES (?, ?, ?, ?)",
            (order_id, item_id, quantity, extra_wishes)
        )

    connection.commit()
    return True


def get_or_create_item(name: str, price: float) -> int:
    """
    Returns the item_id of an existing item matched by name,
    or inserts a new item and returns its id.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT item_id FROM items WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        return row["item_id"]

    cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (name, price))
    connection.commit()
    return cursor.lastrowid


def get_order_with_items(order_id: int) -> dict | None:
    """
    Returns the order as a dict with an 'items' list, or None if not found.
    Each item contains the item name, price, quantity, and extra_wishes.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        return None

    cursor.execute(
        """
        SELECT oi.id, oi.quantity, oi.extra_wishes, i.name, i.price, i.item_id
        FROM order_items oi
        JOIN items i ON oi.item_id = i.item_id
        WHERE oi.order_id=?
        """,
        (order_id,)
    )
    items = [dict(row) for row in cursor.fetchall()]

    order = dict(order_row)
    order["items"] = items
    return order


def close_order(order_id: int) -> bool:
    """Marks an order as 'ordered' (closed). Returns True if a row was updated."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE orders SET status='ordered' WHERE id=? AND status='open'",
        (order_id,)
    )
    connection.commit()
    return cursor.rowcount > 0


def close_all_open_orders() -> int:
    """
    Closes every order that is still 'open'.
    Meant to be called at midnight to end the day's orders.
    Returns the number of orders that were closed.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE orders SET status='ordered' WHERE status='open'")
    connection.commit()
    return cursor.rowcount


def remove_item_from_order(order_id: int, item_id: int) -> bool:
    """Removes all order_items rows for a given item in an order. Returns True if anything was deleted."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM order_items WHERE order_id=? AND item_id=?",
        (order_id, item_id)
    )
    connection.commit()
    return cursor.rowcount > 0


def update_item_in_order(order_id: int, item_id: int, quantity: int, extra_wishes: str = None) -> bool:
    """
    Updates the quantity (and optionally extra_wishes) of an item in an order.
    Returns True if a row was updated.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE order_items SET quantity=?, extra_wishes=? WHERE order_id=? AND item_id=?",
        (quantity, extra_wishes, order_id, item_id)
    )
    connection.commit()
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Guild config
# ---------------------------------------------------------------------------

def setup_guild(guild_id: int, order_channel_id: int, manager_role_id: int) -> None:
    """Saves the complete guild configuration."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO guild_config (guild_id, order_channel_id, manager_role_id) 
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET 
            order_channel_id=excluded.order_channel_id,
            manager_role_id=excluded.manager_role_id
        """,
        (guild_id, order_channel_id, manager_role_id)
    )
    connection.commit()


def get_guild_config(guild_id: int) -> dict | None:
    """Returns the guild config dict, or None if not set up."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM guild_config WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def is_guild_setup(guild_id: int) -> bool:
    """Returns True if the guild has been set up."""
    return get_guild_config(guild_id) is not None


def set_order_channel(guild_id: int, channel_id: int) -> None:
    """Saves (or updates) the order channel for a guild."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO guild_config (guild_id, order_channel_id) VALUES (?, ?) "
        "ON CONFLICT(guild_id) DO UPDATE SET order_channel_id=excluded.order_channel_id",
        (guild_id, channel_id)
    )
    connection.commit()


def get_order_channel(guild_id: int) -> int | None:
    """Returns the configured order channel id for a guild, or None."""
    config = get_guild_config(guild_id)
    return config["order_channel_id"] if config else None


def get_manager_role(guild_id: int) -> int | None:
    """Returns the configured manager role id for a guild, or None."""
    config = get_guild_config(guild_id)
    return config["manager_role_id"] if config else None


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def get_all_items() -> list[dict]:
    """Returns all items in the menu."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM items ORDER BY name")
    return [dict(row) for row in cursor.fetchall()]


def create_item(name: str, price: float, description: str = None) -> dict:
    """Inserts a new item and returns it. Raises ValueError if name already exists."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT item_id FROM items WHERE name=?", (name,))
    if cursor.fetchone():
        raise ValueError(f"Item '{name}' already exists.")
    cursor.execute("INSERT INTO items (name, price, description) VALUES (?, ?, ?)", (name, price, description))
    connection.commit()
    return {"item_id": cursor.lastrowid, "name": name, "price": price, "description": description}


def delete_item(name: str) -> bool:
    """Deletes an item by name. Returns True if deleted, False if not found."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM items WHERE name=?", (name,))
    connection.commit()
    return cursor.rowcount > 0


def get_item_by_name(name: str) -> dict | None:
    """Returns an item by name, or None if not found."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM items WHERE name=?", (name,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_stats() -> dict:
    """Returns various statistics about orders."""
    connection = get_connection()
    cursor = connection.cursor()

    # Total orders
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()["count"]

    # Orders by status
    cursor.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status")
    orders_by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Total revenue (from completed/ordered orders)
    cursor.execute("""
        SELECT COALESCE(SUM(i.price * oi.quantity), 0) as total
        FROM order_items oi
        JOIN items i ON oi.item_id = i.item_id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'ordered'
    """)
    total_revenue = cursor.fetchone()["total"]

    # Most popular items
    cursor.execute("""
        SELECT i.name, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN items i ON oi.item_id = i.item_id
        GROUP BY i.item_id
        ORDER BY total_quantity DESC
        LIMIT 5
    """)
    popular_items = [{"name": row["name"], "quantity": row["total_quantity"]} for row in cursor.fetchall()]

    # Total users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()["count"]

    # Orders today
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE date(date) = date('now')")
    orders_today = cursor.fetchone()["count"]

    # Current open orders breakdown (items grouped by name + extra_wishes)
    cursor.execute("""
        SELECT i.name, oi.extra_wishes, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN items i ON oi.item_id = i.item_id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'open'
        GROUP BY i.name, oi.extra_wishes
        ORDER BY total_quantity DESC
    """)
    current_open_items = []
    for row in cursor.fetchall():
        name = row["name"]
        if row["extra_wishes"]:
            name += f" ({row['extra_wishes']})"
        current_open_items.append({
            "name": name,
            "quantity": row["total_quantity"]
        })

    # Closed/ordered items breakdown (items grouped by name + extra_wishes)
    cursor.execute("""
        SELECT i.name, oi.extra_wishes, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN items i ON oi.item_id = i.item_id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'ordered'
        GROUP BY i.name, oi.extra_wishes
        ORDER BY total_quantity DESC
    """)
    closed_items = []
    for row in cursor.fetchall():
        name = row["name"]
        if row["extra_wishes"]:
            name += f" ({row['extra_wishes']})"
        closed_items.append({
            "name": name,
            "quantity": row["total_quantity"]
        })

    return {
        "total_orders": total_orders,
        "orders_by_status": orders_by_status,
        "total_revenue": total_revenue,
        "popular_items": popular_items,
        "total_users": total_users,
        "orders_today": orders_today,
        "current_open_items": current_open_items,
        "closed_items": closed_items,
    }


# ---------------------------------------------------------------------------
# Admin order management
# ---------------------------------------------------------------------------

def get_all_open_orders_with_users() -> list[dict]:
    """
    Returns every open order together with the user info and its items.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT o.id, o.user_id, o.date, u.username
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE o.status='open'
        ORDER BY o.date
        """
    )
    orders = [dict(row) for row in cursor.fetchall()]
    for order in orders:
        cursor.execute(
            """
            SELECT oi.quantity, oi.extra_wishes, i.name, i.price
            FROM order_items oi
            JOIN items i ON oi.item_id = i.item_id
            WHERE oi.order_id=?
            """,
            (order["id"],)
        )
        order["items"] = [dict(row) for row in cursor.fetchall()]
    return orders


def cancel_all_open_orders() -> list[int]:
    """
    Sets all open orders to 'cancelled' and returns the list of affected user_ids.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM orders WHERE status='open'")
    user_ids = [row["user_id"] for row in cursor.fetchall()]
    cursor.execute("UPDATE orders SET status='cancelled' WHERE status='open'")
    connection.commit()
    return user_ids


if __name__ == "__main__":
    init_db()
    get_or_create_user(123, "Test User", "https://example.com/avatar.jpg")
