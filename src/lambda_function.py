import json
import os
from dataclasses import asdict

import httpx
import asyncio
import boto3
from botocore.client import BaseClient
from loguru import logger
from dotenv import load_dotenv


from src.data_service import DataService
from src.models import User, Settings, UserSpotifyData

load_dotenv(".env")

def get_settings() -> Settings:
    logger.info("Loading environment settings")
    data_api_base_url = os.environ["DATA_API_BASE_URL"]
    request_timeout = float(os.environ["REQUEST_TIMEOUT"])
    queue_url = os.environ["QUEUE_URL"]

    settings = Settings(data_api_base_url=data_api_base_url, request_timeout=request_timeout, queue_url=queue_url)

    logger.debug(f"Setting extracted from environment: {settings}")

    return settings


def get_user_data_from_event(event: dict) -> User:
    logger.info("Extracting user data from event")
    logger.debug(f"Event received: {event}")
    record = event["Records"][0]
    data = json.loads(record["body"])
    user = User(id=data["user_id"], refresh_token=data["refresh_token"])
    logger.debug(f"Extracted user: {user}")
    return user


def add_user_spotify_data_to_queue(
        sqs: BaseClient,
        queue_url: str,
        user_id: str,
        user_spotify_data: UserSpotifyData
):
    logger.info("Sending message to SQS")
    message_data = {
        "user_id": user_id,
        "refresh_token": user_spotify_data.refresh_token,
        "top_artists_data": [asdict(entry) for entry in user_spotify_data.top_artists_data],
        "top_tracks_data": [asdict(entry) for entry in user_spotify_data.top_tracks_data],
        "top_genres_data": [asdict(entry) for entry in user_spotify_data.top_genres_data],
        "top_emotions_data": [asdict(entry) for entry in user_spotify_data.top_emotions_data],
    }
    message = json.dumps(message_data)
    logger.debug(f"Message being sent: {message}")
    res = sqs.send_message(QueueUrl=queue_url, MessageBody=message)
    logger.info(f"Message sent. SQS response: {res}")


async def main(event):
    settings = get_settings()
    user = get_user_data_from_event(event)

    client = httpx.AsyncClient()

    try:
        spotify_service = DataService(
            client=client,
            data_api_base_url=settings.data_api_base_url,
            request_timeout=settings.request_timeout
        )

        user_spotify_data = await spotify_service.get_user_spotify_data(user.refresh_token)
        print(user_spotify_data)
    except Exception as e:
        logger.error(f"Something went wrong - {e}")
        raise
    finally:
        await client.aclose()

    sqs = boto3.client("sqs")
    add_user_spotify_data_to_queue(
        sqs=sqs,
        queue_url=settings.queue_url,
        user_id=user.id,
        user_spotify_data=user_spotify_data
    )


def lambda_handler(event, context):
    asyncio.run(main(event))
