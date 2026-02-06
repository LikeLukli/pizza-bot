import json

from pathlib import Path
from models.order import Order, Item

DATA_FILE = Path("services/data.json")

def load_orders() -> list[Order]:
    if not DATA_FILE.exists():
        return []

    orders = []
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)

    for order in raw:
        order = Order(
            id=order["id"],
            user_id=order["user_id"],
            items=[Item(**item) for item in order["items"]],
            status=order["status"]
        )
        orders.append(order)

    return orders

def save_orders(order: list[Order]):
    DATA_FILE.parent.mkdir(exist_ok=True)

    with open(DATA_FILE, "w") as f:
        json.dump([
            {
                "id": o.id,
                "user_id": o.user_id,
                "items": [
                    {"name": i.name, "quantity": i.quantity}
                    for i in o.items
                ]

            }
            for o in order
        ])