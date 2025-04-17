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
class Settings:
    spotify_client_id: str
    spotify_client_secret: str
    spotify_auth_base_url: str
    spotify_data_base_url: str
    queue_url: str


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
    time_range: TimeRange


@dataclass
class UserSpotifyData:
    refresh_token: str
    top_artists_data: list[TopItemsData]
    top_tracks_data: list[TopItemsData]
