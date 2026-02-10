import sqlite3
from models.order import Order, Item

_connection = None

def get_connection(filename="./data/db/orders.db"):
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(filename)
        _connection.row_factory = sqlite3.Row

    return _connection


def init_db():
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
        item_id TEXT PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATETIME NOT NULL,
        status TEXT NOT NULL
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id TEXT NOT NULL,
        extra_wishes TEXT,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id)
        FOREIGN KEY (item_id) REFERENCES items(item_id))
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