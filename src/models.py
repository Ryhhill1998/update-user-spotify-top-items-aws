from enum import Enum
from dataclasses import dataclass


class ItemType(str, Enum):
    ARTIST = "artist"
    TRACK = "track"
    GENRE = "genre"
    EMOTION = "emotion"


class TimeRange(str, Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


@dataclass
class Settings:
    data_api_base_url: str
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
class TopArtist:
    id: str
    position: int


@dataclass
class TopTrack:
    id: str
    position: int


@dataclass
class TopGenre:
    name: str
    count: int


@dataclass
class TopEmotion:
    name: str
    percentage: float


@dataclass
class TopArtistsData:
    top_artists: list[TopArtist]
    time_range: TimeRange


@dataclass
class TopTracksData:
    top_tracks: list[TopTrack]
    time_range: TimeRange


@dataclass
class TopGenresData:
    top_genres: list[TopGenre]
    time_range: TimeRange


@dataclass
class TopEmotionsData:
    top_emotions: list[TopEmotion]
    time_range: TimeRange


@dataclass
class UserSpotifyData:
    refresh_token: str | None
    top_artists_data: list[TopArtistsData]
    top_tracks_data: list[TopTracksData]
    top_genres_data: list[TopGenresData]
    top_emotions_data: list[TopEmotionsData]
