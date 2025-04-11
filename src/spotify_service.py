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
    refresh_token: str | None = None


@dataclass
class TopItem:
    id: str
    position: int


@dataclass
class TopItemsData:
    top_items: list[TopItem]
    item_type: str
    time_range: str


class SpotifyService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def refresh_tokens(self, url: str, client_id: str, client_secret: str, refresh_token: str) -> Tokens:
        credentials = f"{client_id}:{client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        res = await self.client.post(url=url, headers=headers, data=data)
        res.raise_for_status()
        token_data = res.json()

        refreshed_tokens = Tokens(**token_data)
        return refreshed_tokens

    async def get_top_items(
            self,
            base_url: str,
            access_token: str,
            item_type: str,
            time_range: str
    ) -> TopItemsData:
        url = f"{base_url}/{item_type}"
        params = {"time_range": time_range, "limit": 50}

        res = await self.client.get(url=url, params=params, headers={"Authorization": f"Bearer {access_token}"})
        res.raise_for_status()
        data = res.json()

        top_items_data = data["items"]
        top_items = [TopItem(id=entry["id"], position=index + 1) for index, entry in enumerate(top_items_data)]
        top_items = TopItemsData(top_items=top_items, item_type=item_type, time_range=time_range)
        return top_items
