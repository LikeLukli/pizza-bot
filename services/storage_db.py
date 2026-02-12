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
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATETIME NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        extra_wishes TEXT,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
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

#TODO
def get_or_create_user(user_id: int, username: str, avatar_url: str) -> dict:
    pass

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