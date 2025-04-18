import os
from unittest import mock

import pytest

from src.lambda_function import get_user_data_from_event, get_settings
from src.models import User, Settings


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
    pass


def test_main():
    pass
