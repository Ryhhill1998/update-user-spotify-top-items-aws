import asyncio
import base64

from loguru import logger
import httpx
from httpx import Response

from src.models import Tokens, ItemType, TimeRange, TopItemsData, TopItem, UserSpotifyData


class SpotifyServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class SpotifyService:
    def __init__(
            self,
            client: httpx.AsyncClient,
            client_id: str,
            client_secret: str,
            auth_url: str,
            data_base_url: str
    ):
        self.client = client
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.data_base_url = data_base_url

    async def _make_request(self, method: str, url: str, **kwargs):
        try:
            res = await self.client.request(method, url, **kwargs)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_message = "Unauthorised API request"
            else:
                error_message = "Unsuccessful API response"

            logger.error(f"{error_message} - {e}")
            raise SpotifyServiceException(error_message)
        except httpx.RequestError as e:
            error_message = "Failed to make API request"
            logger.error(f"{error_message} - {e}")
            raise SpotifyServiceException(error_message)

    async def _refresh_tokens(self, refresh_token: str) -> Tokens:
        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        token_data = await self._make_request(method="POST", url=self.auth_url, headers=headers, data=data)

        tokens = Tokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token")
        )
        return tokens

    async def _get_top_items(self, access_token: str, item_type: ItemType, time_range: TimeRange) -> TopItemsData:
        url = f"{self.data_base_url}/me/top/{item_type.value}s"
        params = {"time_range": time_range.value, "limit": 50}

        data = await self._make_request(
            method="GET",
            url=url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        top_items_data = data["items"]
        top_items = [TopItem(id=entry["id"], position=index + 1) for index, entry in enumerate(top_items_data)]
        top_items = TopItemsData(top_items=top_items, item_type=item_type, time_range=time_range)
        return top_items

    async def _get_all_top_items(self, access_token: str) -> list[TopItemsData]:
        tasks = []

        for time_range in TimeRange:
            for item_type in ItemType:
                get_top_items_task = self._get_top_items(
                    access_token=access_token,
                    item_type=item_type,
                    time_range=time_range
                )
                tasks.append(get_top_items_task)

        all_top_items = await asyncio.gather(*tasks)
        return all_top_items

    async def get_user_spotify_data(self, refresh_token: str) -> UserSpotifyData:
        tokens = await self._refresh_tokens(refresh_token)
        all_top_items = await self._get_all_top_items(tokens.access_token)
        user_spotify_data = UserSpotifyData(refresh_token=tokens.refresh_token, data=all_top_items)
        return user_spotify_data
