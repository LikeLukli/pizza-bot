import sqlite3
import os
from pathlib import Path
from models.order import Order, Item

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

    if not os.path.exists(filename):
        os.makedirs(os.path.dirname(filename))

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
        price REAL NOT NULL
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
    pass

def create_order(user_id: int) -> int:
    pass

def add_item_to_order(order_id: int, item_id: int, quantity: int, extra_wishes: str) -> bool:
    pass

def get_or_create_item(name: str, price: float) -> int:
    pass

def get_order_with_items(order_id: int) -> dict | None:
    pass

def close_order(order_id: int) -> bool:
    pass

def remove_item_from_order(order_id: int, item_id: int) -> bool:
    pass

def update_item_in_order(order_id: int, item_id: int, quantity: int, extra_wishes: str) -> bool:
    pass

if __name__ == "__main__":
    init_db()
    get_or_create_user(123, "Test User", "https://example.com/avatar.jpg")
