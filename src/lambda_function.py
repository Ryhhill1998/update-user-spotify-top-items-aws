import json
import os
import httpx
import mysql.connector
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from src.db_service import DBService
from src.spotify_service import SpotifyService, TimeRange, ItemType


@dataclass
class User:
    id: str
    refresh_token: str


def get_user_data_from_event(event: dict):
    record = event["Records"][0]
    data = json.loads(record["body"])
    user = User(id=data["user_id"], refresh_token=data["refresh_token"])
    return user


async def get_user_top_items_data_for_all_time_ranges(spotify_service: SpotifyService, access_token: str):
    tasks = []

    for time_range in TimeRange:
        for item_type in ItemType:
            get_top_items_task = spotify_service.get_top_items(
                base_url=f"{os.environ.get("SPOTIFY_DATA_BASE_URL")}/me/top",
                access_token=access_token,
                item_type=item_type.value,
                time_range=time_range.value
            )
            tasks.append(get_top_items_task)

    all_top_items = await asyncio.gather(*tasks)
    return all_top_items


async def main(event):
    # Create required classes
    client = httpx.AsyncClient()
    spotify_service = SpotifyService(client)

    connection = mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS")
    )
    db_service = DBService(connection)

    # 1. Get user_id and refresh_token from event records
    user = get_user_data_from_event(event)

    # 2. Refresh user's access_token to Spotify API using refresh_token.
    tokens = await spotify_service.refresh_tokens(
        url=f"{os.environ.get("SPOTIFY_AUTH_BASE_URL")}/api/token",
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        refresh_token=user.refresh_token
    )

    # 3. If new refresh_token is returned, update it in the DB.
    if tokens.refresh_token is not None:
        db_service.update_refresh_token(user_id=user.id, refresh_token=tokens.refresh_token)

    # 4. Get user's top artists and tracks from Spotify API for all time ranges.
    all_top_items_data = await get_user_top_items_data_for_all_time_ranges(
        spotify_service=spotify_service,
        access_token=tokens.access_token
    )

    # 5. Store all top items in DB.
    collected_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    for top_items_data in all_top_items_data:
        db_service.store_top_items(user_id=user.id, top_items_data=top_items_data, collected_date=collected_date)


def lambda_handler(event, context):
    asyncio.run(main(event))
