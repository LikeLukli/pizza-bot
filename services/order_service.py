from services import storage


def add_item(user_id: int, username: str, avatar_url: str,
             item_name: str, item_price: float,
             quantity: int = 1, extra_wishes: str = None) -> dict:
    """
    Main entry point for ordering.
    - Ensures the user exists in the DB.
    - Gets the user's current open order, or creates a new one.
    - Resolves the item (get or create).
    - Adds the item to the order.
    Returns a summary dict with order_id and the item that was added.
    """
    storage.get_or_create_user(user_id, username, avatar_url)

    order = storage.get_user_open_order(user_id)
    if order is None:
        order_id = storage.create_order(user_id)
    else:
        order_id = order["id"]

    item_id = storage.get_or_create_item(item_name, item_price)
    storage.add_item_to_order(order_id, item_id, quantity, extra_wishes)

    return {
        "order_id": order_id,
        "item": item_name,
        "quantity": quantity,
        "extra_wishes": extra_wishes,
    }


def get_current_order(user_id: int) -> dict | None:
    """
    Returns the full open order (with items) for a user, or None if they have none.
    """
    order = storage.get_user_open_order(user_id)
    if order is None:
        return None
    return storage.get_order_with_items(order["id"])


def remove_item(user_id: int, item_name: str) -> bool:
    """
    Removes an item by name from the user's open order.
    Returns True on success, False if there is no open order or item wasn't found.
    """
    order = storage.get_user_open_order(user_id)
    if order is None:
        return False

    full_order = storage.get_order_with_items(order["id"])
    matched = next((i for i in full_order["items"] if i["name"].lower() == item_name.lower()), None)
    if matched is None:
        return False

    return storage.remove_item_from_order(order["id"], matched["item_id"])


def close_daily_orders() -> int:
    """
    Closes all open orders. Call this at midnight.
    Returns the number of orders that were closed.
    """
    return storage.close_all_open_orders()


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def get_all_open_orders() -> list[dict]:
    """Returns all open orders with user info and items for admin display."""
    return storage.get_all_open_orders_with_users()


def cancel_daily_orders() -> list[int]:
    """
    Cancels all open orders and returns the list of affected user_ids.
    """
    return storage.cancel_all_open_orders()


def create_menu_item(name: str, price: float, description: str = None) -> dict:
    """Creates a new menu item. Raises ValueError if it already exists."""
    return storage.create_item(name, price, description)


def delete_menu_item(name: str) -> bool:
    """Deletes a menu item by name. Returns True if deleted."""
    return storage.delete_item(name)


def get_menu_items() -> list[dict]:
    """Returns all menu items."""
    return storage.get_all_items()


def get_stats() -> dict:
    """Returns order statistics."""
    return storage.get_stats()


def setup_guild(guild_id: int, channel_id: int, role_id: int) -> None:
    storage.setup_guild(guild_id, channel_id, role_id)


def get_guild_config(guild_id: int) -> dict | None:
    return storage.get_guild_config(guild_id)


def is_guild_setup(guild_id: int) -> bool:
    return storage.is_guild_setup(guild_id)


def set_order_channel(guild_id: int, channel_id: int) -> None:
    storage.set_order_channel(guild_id, channel_id)


def get_order_channel(guild_id: int) -> int | None:
    return storage.get_order_channel(guild_id)


def get_manager_role(guild_id: int) -> int | None:
    return storage.get_manager_role(guild_id)


