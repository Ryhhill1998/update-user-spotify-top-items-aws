import uuid

import pytest

from src.lambda_function import get_user_data_from_event
from src.models import User


def test_get_settings():
    pass


def test_get_user_data_from_event():
    mock_event = {"Records": [{"body": "{\"user_id\": \"123\", \"refresh_token\": \"abc\"}"}]}

    user = get_user_data_from_event(mock_event)

    assert user == User(id="123", refresh_token="abc")


def test_add_user_spotify_data_to_queue():
    pass


def test_main():
    pass
