import json
import logging

from pathlib import Path
from models.order import Order, Item

BOT_LOGGER = logging.getLogger(__name__)

def load_orders(data_file: Path ) -> list[Order]:
    BOT_LOGGER.info("Loading orders...")
    if not data_file.exists():
        BOT_LOGGER.info("Data file not found. Returning empty array...")
        return []

    orders = []
    BOT_LOGGER.info(f"Data file found. Loading orders from {data_file}...")
    with open(data_file, "r") as f:
        raw = json.load(f)

    BOT_LOGGER.info(f"Loaded {len(raw)} orders.")
    for order in raw:
        order = Order(
            id=order["id"],
            user_id=order["user_id"],
            items=[Item(**item) for item in order["items"]],
            status=order["status"]
        )
        orders.append(order)

    return orders

def save_orders(order: list[Order], data_file: Path) -> None:
    data_file.parent.mkdir(exist_ok=True)

    with open(data_file, "w") as f:
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
        ], f, indent=4)