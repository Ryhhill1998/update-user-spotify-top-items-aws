import json
import os
from dataclasses import asdict

import boto3
import httpx
import asyncio

from botocore.client import BaseClient

from spotify_service import SpotifyService, TimeRange, ItemType, TopItemsData
from src.models import User, Settings


def get_user_data_from_event(event: dict) -> User:
    record = event["Records"][0]
    data = json.loads(record["body"])
    user = User(id=data["user_id"], refresh_token=data["refresh_token"])
    return user


async def fetch_all_top_items(
        spotify_service: SpotifyService,
        spotify_data_base_url: str,
        access_token: str
) -> list[TopItemsData]:
    tasks = []

    for time_range in TimeRange:
        for item_type in ItemType:
            get_top_items_task = spotify_service.get_top_items(
                base_url=f"{spotify_data_base_url}/me/top",
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


async def get_user_spotify_data(settings: Settings, user: User):
    client = httpx.AsyncClient()

    try:
        spotify_service = SpotifyService(client)

        # 1. Refresh access token
        tokens = await spotify_service.refresh_tokens(
            url=f"{settings.spotify_auth_base_url}/api/token",
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            refresh_token=user.refresh_token
        )

        # 2. Fetch top items
        all_top_items_data = await fetch_all_top_items(
            spotify_service=spotify_service,
            spotify_data_base_url=f"{settings.spotify_data_base_url}/me/top",
            access_token=tokens.access_token
        )
        return all_top_items_data, tokens.refresh_token
    except Exception as e:
        print(f"Something went wrong - {e}")
    finally:
        await client.aclose()


def lambda_handler(event, context):
    spotify_client_id = os.environ["SPOTIFY_CLIENT_ID"]
    spotify_client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    spotify_auth_base_url = os.environ["SPOTIFY_AUTH_BASE_URL"]
    spotify_data_base_url = os.environ["SPOTIFY_DATA_BASE_URL"]
    queue_url = os.environ["QUEUE_URL"]

    settings = Settings(
        spotify_client_id=spotify_client_id,
        spotify_client_secret=spotify_client_secret,
        spotify_auth_base_url=spotify_auth_base_url,
        spotify_data_base_url=spotify_data_base_url,
        queue_url=queue_url
    )

    user = get_user_data_from_event(event)

    all_top_items_data, refresh_token = asyncio.run(get_user_spotify_data(settings=settings, user=user))

    sqs = boto3.client("sqs")
    add_user_spotify_data_to_queue(
        sqs=sqs,
        queue_url=settings.queue_url,
        user_id=user.id,
        refresh_token=refresh_token,
        all_top_items_data=all_top_items_data
    )
