import json
import os
from dataclasses import asdict

import boto3
import httpx
import asyncio

from botocore.client import BaseClient

from spotify_service import SpotifyService, TimeRange, ItemType, TopItemsData
from src.models import User

# Extract environment variables
SPOTIFY_CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_AUTH_BASE_URL = os.environ["SPOTIFY_AUTH_BASE_URL"]
SPOTIFY_DATA_BASE_URL = os.environ["SPOTIFY_DATA_BASE_URL"]
QUEUE_URL = os.environ.get("QUEUE_URL")


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


def add_user_spotify_data_to_queue(
        sqs: BaseClient,
        queue_url: str,
        user_id: str,
        refresh_token: str,
        all_top_items_data: list[TopItemsData]
):
    message_data = {
        "user_id": user_id,
        "refresh_token": refresh_token,
        "all_top_items_data": [asdict(entry) for entry in all_top_items_data]
    }
    message = json.dumps(message_data)
    res = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    print(f"{res = }")


async def main(event):
    client = httpx.AsyncClient()

    try:
        spotify_service = SpotifyService(client)
        # create sqs connection
        sqs = boto3.client("sqs")

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
        add_user_spotify_data_to_queue(
            sqs=sqs,
            queue_url=QUEUE_URL,
            user_id=user.id,
            refresh_token=tokens.refresh_token,
            all_top_items_data=all_top_items_data
        )
    except Exception as e:
        print(f"Something went wrong - {e}")
    finally:
        # 5. Close http connection.
        await client.aclose()


def lambda_handler(event, context):
    asyncio.run(main(event))
