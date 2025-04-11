import base64
import httpx
from enum import Enum
from dataclasses import dataclass


class ItemType(Enum):
    ARTISTS = "artists"
    TRACKS = "tracks"


class TimeRange(Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


@dataclass
class Tokens:
    access_token: str
    refresh_token: str


class SpotifyService:
    def __init__(self, client: httpx.AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url

    async def refresh_tokens(self, client_id: str, client_secret: str, refresh_token: str) -> Tokens:
        url = f"{self.base_url}/api/token"
        headers = {
            "Authorization": f"Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        res = await self.client.post(url=url, headers=headers, data=data)
        res.raise_for_status()
        token_data = res.json()

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", refresh_token)
        refreshed_tokens = Tokens(access_token=access_token, refresh_token=refresh_token)

        return refreshed_tokens


    async def _get_top_items(self, access_token: str, item_type: ItemType, time_range: TimeRange) -> list[dict]:
        url = f"{self.base_url}/me/top/{item_type.value}"
        params = {"time_range": time_range, "limit": 50}

        res = await self.client.get(url=url, params=params, headers={"Authorization": f"Bearer {access_token}"})
        res.raise_for_status()
        data = res.json()

        top_items = data["items"]
        return top_items

    async def get_top_artists_ids(self, access_token: str, time_range: TimeRange) -> list[str]:
        top_artists_data = await self._get_top_items(
            access_token=access_token,
            item_type=ItemType.TRACKS,
            time_range=time_range
        )
        top_artists_ids = [entry["id"] for entry in top_artists_data]
        return top_artists_ids

    async def get_top_tracks_ids(self, access_token: str, time_range: TimeRange) -> list[str]:
        top_tracks_data = await self._get_top_items(
            access_token=access_token,
            item_type=ItemType.TRACKS,
            time_range=time_range
        )
        top_tracks_ids = [entry["id"] for entry in top_tracks_data]
        return top_tracks_ids
