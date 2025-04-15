from enum import Enum
from dataclasses import dataclass


class ItemType(Enum):
    ARTIST = "artist"
    TRACK = "track"


class TimeRange(Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


@dataclass
class User:
    id: str
    refresh_token: str


@dataclass
class Tokens:
    access_token: str
    refresh_token: str | None = None


@dataclass
class TopItem:
    id: str
    position: int


@dataclass
class TopItemsData:
    top_items: list[TopItem]
    item_type: ItemType
    time_range: TimeRange
