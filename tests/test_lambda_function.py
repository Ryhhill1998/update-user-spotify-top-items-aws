import json
import os
import uuid
from unittest import mock
from unittest.mock import Mock

import pytest

from src.lambda_function import get_user_data_from_event, get_settings, add_user_spotify_data_to_queue
from src.models import User, Settings, UserSpotifyData, TopItemsData, TopItem, TimeRange


@pytest.fixture
def mock_settings(monkeypatch):
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "SPOTIFY_CLIENT_ID": "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET": "SPOTIFY_CLIENT_SECRET",
            "SPOTIFY_AUTH_BASE_URL": "SPOTIFY_AUTH_BASE_URL",
            "SPOTIFY_DATA_BASE_URL": "SPOTIFY_DATA_BASE_URL",
            "QUEUE_URL": "QUEUE_URL"
        }
        for key, value in envvars.items():
            monkeypatch.setenv(key, value)

        yield


def test_get_settings(mock_settings):
    expected_settings = Settings(
        spotify_client_id="SPOTIFY_CLIENT_ID",
        spotify_client_secret="SPOTIFY_CLIENT_SECRET",
        spotify_auth_base_url="SPOTIFY_AUTH_BASE_URL",
        spotify_data_base_url="SPOTIFY_DATA_BASE_URL",
        queue_url="QUEUE_URL"
    )

    settings = get_settings()

    assert settings == expected_settings


def test_get_user_data_from_event():
    mock_event = {"Records": [{"body": "{\"user_id\": \"123\", \"refresh_token\": \"abc\"}"}]}

    user = get_user_data_from_event(mock_event)

    assert user == User(id="123", refresh_token="abc")


def test_add_user_spotify_data_to_queue():
    mock_sqs = Mock()
    mock_send_message = Mock()
    mock_send_message.return_value = None
    mock_sqs.send_message = mock_send_message
    queue_url = "test"
    user_id = str(uuid.uuid4())
    refresh_token = str(uuid.uuid4())
    user_spotify_data = UserSpotifyData(
        refresh_token=refresh_token,
        top_artists_data=[
            TopItemsData(
                top_items=[
                    TopItem(id="1", position=1),
                    TopItem(id="2", position=2),
                    TopItem(id="3", position=3),
                ],
                time_range=TimeRange.SHORT
            ),
            TopItemsData(
                top_items=[
                    TopItem(id="1", position=1),
                    TopItem(id="2", position=2),
                    TopItem(id="3", position=3),
                ],
                time_range=TimeRange.MEDIUM
            ),
            TopItemsData(
                top_items=[
                    TopItem(id="1", position=1),
                    TopItem(id="2", position=2),
                    TopItem(id="3", position=3),
                ],
                time_range=TimeRange.LONG
            )
        ],
        top_tracks_data=[
            TopItemsData(
                top_items=[
                    TopItem(id="1", position=1),
                    TopItem(id="2", position=2),
                    TopItem(id="3", position=3),
                ],
                time_range=TimeRange.SHORT
            ),
            TopItemsData(
                top_items=[
                    TopItem(id="1", position=1),
                    TopItem(id="2", position=2),
                    TopItem(id="3", position=3),
                ],
                time_range=TimeRange.MEDIUM
            ),
            TopItemsData(
                top_items=[
                    TopItem(id="1", position=1),
                    TopItem(id="2", position=2),
                    TopItem(id="3", position=3),
                ],
                time_range=TimeRange.LONG
            )
        ]
    )

    add_user_spotify_data_to_queue(
        sqs=mock_sqs,
        queue_url=queue_url,
        user_id=user_id,
        user_spotify_data=user_spotify_data
    )

    expected_message_data = {
        "user_id": user_id,
        "refresh_token": refresh_token,
        "top_artists_data": [
            {
                "top_items": [
                    {
                        "id": "1",
                        "position": 1
                    },
                    {
                        "id": "2",
                        "position": 2
                    },
                    {
                        "id": "3",
                        "position": 3
                    }
                ],
                "time_range": "short_term"
            },
            {
                "top_items": [
                    {
                        "id": "1",
                        "position": 1
                    },
                    {
                        "id": "2",
                        "position": 2
                    },
                    {
                        "id": "3",
                        "position": 3
                    }
                ],
                "time_range": "medium_term"
            },
            {
                "top_items": [
                    {
                        "id": "1",
                        "position": 1
                    },
                    {
                        "id": "2",
                        "position": 2
                    },
                    {
                        "id": "3",
                        "position": 3
                    }
                ],
                "time_range": "long_term"
            }
        ],
        "top_tracks_data": [
            {
                "top_items": [
                    {
                        "id": "1",
                        "position": 1
                    },
                    {
                        "id": "2",
                        "position": 2
                    },
                    {
                        "id": "3",
                        "position": 3
                    }
                ],
                "time_range": "short_term"
            },
            {
                "top_items": [
                    {
                        "id": "1",
                        "position": 1
                    },
                    {
                        "id": "2",
                        "position": 2
                    },
                    {
                        "id": "3",
                        "position": 3
                    }
                ],
                "time_range": "medium_term"
            },
            {
                "top_items": [
                    {
                        "id": "1",
                        "position": 1
                    },
                    {
                        "id": "2",
                        "position": 2
                    },
                    {
                        "id": "3",
                        "position": 3
                    }
                ],
                "time_range": "long_term"
            }
        ]
    }
    expected_message = json.dumps(expected_message_data)
    mock_send_message.assert_called_once_with(QueueUrl=queue_url, MessageBody=expected_message)
