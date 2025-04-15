import json
import os

import httpx
import asyncio

from spotify_service import SpotifyService, TimeRange, ItemType, TopItemsData
from src.models import User

# Extract environment variables
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_AUTH_BASE_URL = os.environ["SPOTIFY_AUTH_BASE_URL"]
SPOTIFY_DATA_BASE_URL = os.environ["SPOTIFY_DATA_BASE_URL"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]


def get_user_data_from_event(event: dict) -> User:
    record = event["Records"][0]
    data = json.loads(record["body"])
    user = User(id=data["id"], refresh_token=data["refresh_token"])
    return user


async def get_user_top_items_data_for_all_time_ranges(
        spotify_service: SpotifyService,
        access_token: str
) -> list[TopItemsData]:
    tasks = []

    for time_range in TimeRange:
        for item_type in ItemType:
            get_top_items_task = spotify_service.get_top_items(
                base_url=f"{SPOTIFY_DATA_BASE_URL}/me/top",
                access_token=access_token,
                item_type=item_type,
                time_range=time_range
            )
            tasks.append(get_top_items_task)

    all_top_items = await asyncio.gather(*tasks)
    return all_top_items


async def main(event):
    client = httpx.AsyncClient()

    try:
        spotify_service = SpotifyService(client)

        # 1. Get user_id and refresh_token from event records
        user = get_user_data_from_event(event)
        print(f"{user = }")

        # 2. Refresh user's access_token to Spotify API using refresh_token.
        tokens = await spotify_service.refresh_tokens(
            url=f"{SPOTIFY_AUTH_BASE_URL}/api/token",
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            refresh_token=user.refresh_token
        )
        print(f"{tokens = }")

        # 3. Get user's top artists and tracks from Spotify API for all time ranges.
        all_top_items_data = await get_user_top_items_data_for_all_time_ranges(
            spotify_service=spotify_service,
            access_token=tokens.access_token
        )
        print(f"{all_top_items_data = }")

        # 4. Add user Spotify data to SQS queue
    except Exception as e:
        print(f"Something went wrong - {e}")
    finally:
        # 5. Close http connection.
        await client.aclose()


def lambda_handler(event, context):
    asyncio.run(main(event))
