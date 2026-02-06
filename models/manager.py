import logging

from pathlib import Path
from models.order import Order
from services.storage import load_orders, save_orders

BOT_LOGGER = logging.getLogger(__name__)
DEFAULT_DATA_FILE = "data/orders.json"


class OrderManager:
    data_file: Path
    orders: list[Order]

    def __init__(self, data_file: str = DEFAULT_DATA_FILE, use_database: bool = False):
        # TODO: load orders from database / implement database
        if use_database:
            self.data_file = None
            self.orders = []
            return

        self.data_file = Path(data_file)
        self.orders = load_orders(self.data_file)

    def add_order(self, order: Order):
        if self.data_file is None:
            BOT_LOGGER.warning("Database functionality not implemented yet. Cannot add order.")
            return

        self.orders.append(order)
        BOT_LOGGER.info(f"Added order: {order}")
        save_orders(self.orders, self.data_file)

    def remove_order(self, order_id: int):
        if self.data_file is None:
            BOT_LOGGER.warning("Database functionality not implemented yet. Cannot remove order.")
            return

        order_found = False
        for order in self.orders:
            if order.id == order_id:
                self.orders.remove(order)
                order_found = True
                BOT_LOGGER.info(f"Removed order with ID: {order_id}")
                break

        if not order_found:
            BOT_LOGGER.info(f"Order with ID {order_id} not found")
        else:
            save_orders(self.orders, self.data_file)

    def remove_item(self, order_id: int, item_name: str):
        if self.data_file is None:
            BOT_LOGGER.warning("Database functionality not implemented yet. Cannot remove item.")
            return

        for order in self.orders:
            if order.id == order_id:
                order.items = [i for i in order.items if i.name != item_name]
                BOT_LOGGER.info(f"Removed item '{item_name}' from order ID: {order_id}")
                break
        save_orders(self.orders, self.data_file)