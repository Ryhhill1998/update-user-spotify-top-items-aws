import asyncio

from loguru import logger
import httpx

from src.models import Tokens, ItemType, TimeRange, UserSpotifyData, TopArtist, TopTrack, TopGenre, TopEmotion, \
    TopArtistsData, TopTracksData, TopGenresData, TopEmotionsData


class DataServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DataService:
    def __init__(self, client: httpx.AsyncClient, data_api_base_url: str, request_timeout: float):
        self.client = client
        self.data_api_base_url = data_api_base_url
        self.request_timeout = request_timeout

    async def _get_data_from_api(self, url: str, json_data: dict, params: dict | None = None):
        try:
            logger.info(f"Sending POST request to {url}")
            res = await self.client.post(url=url, params=params, json=json_data, timeout=self.request_timeout)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_message = "Unauthorised API request"
            else:
                error_message = "Unsuccessful API request"

            logger.error(f"{error_message} - {e}")
            raise DataServiceException(error_message)
        except httpx.RequestError as e:
            error_message = "Failed to make API request"
            logger.error(f"{error_message} - {e}")
            raise DataServiceException(error_message)

    async def _refresh_tokens(self, refresh_token: str) -> Tokens:
        url = f"{self.data_api_base_url}/auth/tokens/refresh"
        json_data = {"refresh_token": refresh_token}

        token_data = await self._get_data_from_api(url=url, json_data=json_data)

        try:
            tokens = Tokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token")
            )
            return tokens
        except KeyError as e:
            error_message = f"No access_token present in API response - {e}"
            logger.error(error_message)
            raise DataServiceException(error_message)

    @staticmethod
    def _create_top_items_data(data, item_type: ItemType, time_range: TimeRange):
        try:
            if item_type == ItemType.ARTIST:
                top_artists = [TopArtist(id=entry["id"], position=index + 1) for index, entry in enumerate(data)]
                top_artists_data = TopArtistsData(top_artists=top_artists, time_range=time_range)
                return top_artists_data

            elif item_type == ItemType.TRACK:
                top_tracks = [TopTrack(id=entry["id"], position=index + 1) for index, entry in enumerate(data)]
                top_tracks_data = TopTracksData(top_tracks=top_tracks, time_range=time_range)
                return top_tracks_data

            elif item_type == ItemType.GENRE:
                top_genres = [TopGenre(name=entry["name"], count=entry["count"]) for entry in data]
                top_genres_data = TopGenresData(top_genres=top_genres, time_range=time_range)
                return top_genres_data

            elif item_type == ItemType.EMOTION:
                top_emotions = [TopEmotion(name=entry["name"], percentage=entry["percentage"]) for entry in data]
                top_emotions_data = TopEmotionsData(top_emotions=top_emotions, time_range=time_range)
                return top_emotions_data

            else:
                raise DataServiceException("Invalid item type")
        except KeyError as e:
            error_message = f"Missing field in API data - {e}"
            logger.error(error_message)
            raise DataServiceException(error_message)

    async def _get_top_items_data(self, access_token: str, item_type: ItemType, time_range: TimeRange):
        logger.info(f"Fetching top {item_type}s for time range: {time_range}")

        url = f"{self.data_api_base_url}/data/me/top/{item_type.value}s"
        json_data = {"access_token": access_token}
        params = {"time_range": time_range.value}

        data = await self._get_data_from_api(url=url, json_data=json_data, params=params)
        top_items = self._create_top_items_data(data=data, item_type=item_type, time_range=time_range)

        return top_items

    async def _get_all_top_items(self, access_token: str, item_type: ItemType):
        logger.info(f"Fetching top {item_type}s for all time ranges")

        tasks = [
            self._get_top_items_data(
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

        all_top_genres = await self._get_all_top_items(access_token=tokens.access_token, item_type=ItemType.GENRE)
        logger.debug(f"All top tracks: {all_top_genres}")

        all_top_emotions = await self._get_all_top_items(access_token=tokens.access_token, item_type=ItemType.EMOTION)
        logger.debug(f"All top tracks: {all_top_emotions}")

        user_spotify_data = UserSpotifyData(
            refresh_token=tokens.refresh_token,
            top_artists_data=all_top_artists,
            top_tracks_data=all_top_tracks,
            top_genres_data=all_top_genres,
            top_emotions_data=all_top_emotions
        )
        logger.debug(f"User spotify data: {user_spotify_data}")

        return user_spotify_data
