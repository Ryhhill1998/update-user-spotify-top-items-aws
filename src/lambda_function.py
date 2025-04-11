import json
import os
from enum import Enum

import httpx
import mysql.connector

conn = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    database=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASS")
)


class ItemType(Enum):
    ARTISTS = "artists"
    TRACKS = "tracks"


class TimeRange(Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


# async def get_spotify_top_items(client: , access_token: str, item_type: ItemType, time_range: TimeRange):
#     try:
#         params = {"time_range": time_range, "limit": 50}
#         url = f"{self.base_url}/me/top/{item_type.value}?" + urllib.parse.urlencode(params)
#
#         data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})
#
#         top_items = [self._create_item(data=entry, item_type=item_type) for entry in data["items"]]
#
#         return top_items
#     except EndpointRequesterUnauthorisedException as e:
#         error_message = "Invalid Spotify API access token"
#         logger.error(f"{error_message} - {e}")
#         raise SpotifyDataServiceUnauthorisedException(error_message)
#     except EndpointRequesterException as e:
#         error_message = "Failed to make request to Spotify API"
#         logger.error(f"{error_message} - {e}")
#         raise SpotifyDataServiceException(error_message)


def lambda_handler(event, context):
    records = event["Records"]

    for record in records:
        print(f"{record = }")
        message = json.loads(record["body"])
        print(f"{message = }")

    client = httpx.AsyncClient()
