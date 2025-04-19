import asyncio
import base64

from loguru import logger
import httpx

from src.models import Tokens, ItemType, TimeRange, TopItem, TopItemsData, UserSpotifyData


class SpotifyServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class SpotifyService:
    def __init__(
            self,
            client: httpx.AsyncClient,
            client_id: str,
            client_secret: str,
            auth_base_url: str,
            data_base_url: str
    ):
        self.client = client
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_base_url = auth_base_url
        self.data_base_url = data_base_url

    async def _make_request(self, method: str, url: str, **kwargs):
        try:
            logger.info(f"Sending {method} request to {url}")
            res = await self.client.request(method, url, **kwargs)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_message = "Unauthorised API request"
            else:
                error_message = "Unsuccessful API request"

            logger.error(f"{error_message} - {e}")
            raise SpotifyServiceException(error_message)
        except httpx.RequestError as e:
            error_message = "Failed to make API request"
            logger.error(f"{error_message} - {e}")
            raise SpotifyServiceException(error_message)

    async def _refresh_tokens(self, refresh_token: str) -> Tokens:
        url = f"{self.auth_base_url}/api/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        token_data = await self._make_request(method="POST", url=url, headers=headers, data=data)

        try:
            tokens = Tokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token")
            )
            return tokens
        except KeyError as e:
            error_message = "No access_token present in API response"
            logger.error(f"{error_message} - {e}")
            raise SpotifyServiceException(error_message)

    async def _get_top_items(self, access_token: str, item_type: ItemType, time_range: TimeRange) -> TopItemsData:
        logger.info(f"Fetching top {item_type}s for time range: {time_range}")

        url = f"{self.data_base_url}/me/top/{item_type.value}s"
        params = {"time_range": time_range.value, "limit": 50}

        data = await self._make_request(
            method="GET",
            url=url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        try:
            top_items_data = data["items"]
            top_items = [TopItem(id=entry["id"], position=index + 1) for index, entry in enumerate(top_items_data)]

            if not top_items:
                raise SpotifyServiceException("No top items found")

            top_items = TopItemsData(top_items=top_items, time_range=time_range)
            return top_items
        except KeyError as e:
            error_message = "API response data in unexpected format"
            logger.error(f"{error_message} - {e}")
            raise SpotifyServiceException(error_message)

    async def _get_all_top_items(self, access_token: str, item_type: ItemType) -> list[TopItemsData]:
        logger.info(f"Fetching top {item_type}s for all time ranges")

        tasks = [
            self._get_top_items(
                access_token=access_token,
                item_type=item_type,
                time_range=time_range
            )
            for time_range in TimeRange
        ]

        all_top_items = await asyncio.gather(*tasks)
        return all_top_items

    async def get_user_spotify_data(self, refresh_token: str) -> UserSpotifyData:
        tokens = await self._refresh_tokens(refresh_token)
        logger.debug(f"Tokens: {tokens}")

        all_top_artists = await self._get_all_top_items(access_token=tokens.access_token, item_type=ItemType.ARTIST)
        logger.debug(f"All top artists: {all_top_artists}")

        all_top_tracks = await self._get_all_top_items(access_token=tokens.access_token, item_type=ItemType.TRACK)
        logger.debug(f"All top tracks: {all_top_tracks}")

        user_spotify_data = UserSpotifyData(
            refresh_token=tokens.refresh_token,
            top_artists_data=all_top_artists,
            top_tracks_data=all_top_tracks
        )
        logger.debug(f"User spotify data: {user_spotify_data}")

        return user_spotify_data
