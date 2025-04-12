import json
import os
import httpx
import mysql.connector
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone


from db_service import DBService
from spotify_service import SpotifyService, TimeRange, ItemType, TopItemsData

# Extract environment variables
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_AUTH_BASE_URL = os.environ["SPOTIFY_AUTH_BASE_URL"]
SPOTIFY_DATA_BASE_URL = os.environ["SPOTIFY_DATA_BASE_URL"]
# DB_HOST = os.environ["DB_HOST"]
# DB_NAME = os.environ["DB_NAME"]
# DB_USER = os.environ["DB_USER"]
# DB_PASS = os.environ["DB_PASS"]


@dataclass
class User:
    id: str
    refresh_token: str


def get_user_data_from_event(event: dict) -> User:
    record = event["Records"][0]
    data = json.loads(record["body"])
    user = User(id=data["user_id"], refresh_token=data["refresh_token"])
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
    conn = mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS")
    )

    with conn.cursor() as cur:
        cur.execute("SELECT VERSION();")
        print(cur.fetchone())
    # Create required classes
    # client = httpx.AsyncClient()
    # spotify_service = SpotifyService(client)

    # connection = mysql.connector.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    # db_service = DBService(connection)

    # 1. Get user_id and refresh_token from event records
    # user = get_user_data_from_event(event)

    # 2. Refresh user's access_token to Spotify API using refresh_token.
    # tokens = await spotify_service.refresh_tokens(
    #     url=f"{SPOTIFY_AUTH_BASE_URL}/api/token",
    #     client_id=SPOTIFY_CLIENT_ID,
    #     client_secret=SPOTIFY_CLIENT_SECRET,
    #     refresh_token=user.refresh_token
    # )
    #
    # print(f"{tokens.access_token = }")

    # 3. If new refresh_token is returned, update it in the DB.
    # if tokens.refresh_token is not None:
    #     db_service.update_refresh_token(user_id=user.id, refresh_token=tokens.refresh_token)

    # 4. Get user's top artists and tracks from Spotify API for all time ranges.
    # all_top_items_data = await get_user_top_items_data_for_all_time_ranges(
    #     spotify_service=spotify_service,
    #     access_token=tokens.access_token
    # )

    # 5. Store all top items in DB.
    # collected_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # for top_items_data in all_top_items_data:
    #     for top_item in top_items_data.top_items:
    #         print(f"ID: {top_item.id}, position: {top_item.position}")
        # db_service.store_top_items(user_id=user.id, top_items_data=top_items_data, collected_date=collected_date)

    # 6. Close all connections.
    # await client.aclose()
    # connection.close()


def lambda_handler(event, context):
    asyncio.run(main(event))
