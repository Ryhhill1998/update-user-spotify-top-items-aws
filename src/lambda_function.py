import json
import os
from dataclasses import asdict

import httpx
import asyncio
import boto3
from botocore.client import BaseClient


from spotify_service import SpotifyService, TopItemsData
from src.models import User, Settings


def get_settings() -> Settings:
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

    return settings


def get_user_data_from_event(event: dict) -> User:
    record = event["Records"][0]
    data = json.loads(record["body"])
    user = User(id=data["user_id"], refresh_token=data["refresh_token"])
    return user


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
    settings = get_settings()
    user = get_user_data_from_event(event)

    with httpx.AsyncClient() as client:
        spotify_service = SpotifyService(
            client=client,
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            auth_url=settings.spotify_auth_base_url,
            data_base_url=settings.spotify_data_base_url
        )

        user_spotify_data = await spotify_service.get_user_spotify_data(user.refresh_token)

    sqs = boto3.client("sqs")
    add_user_spotify_data_to_queue(
        sqs=sqs,
        queue_url=settings.queue_url,
        user_id=user.id,
        refresh_token=user_spotify_data.refresh_token,
        all_top_items_data=user_spotify_data.data
    )


def lambda_handler(event, context):
    asyncio.run(main(event))
