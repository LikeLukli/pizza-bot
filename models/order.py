from datetime import date, datetime
from dataclasses import dataclass, field
from typing import List
from enum import Enum
import uuid

class OrderStatus(Enum):
    OPEN = "open"
    ORDERED = "ordered"

@dataclass
class Item:
    name: str
    quantity: int

@dataclass
class Order:
    id: str
    user: User
    items: List[Item] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN
    date: date = date.today()

    @staticmethod
    def create(user_id: int, user: User):
        return Order(
            id=str(uuid.uuid4()),
            user=user
        )

@dataclass
class User:
    user_id: int
    username: str
    avatar_url: str