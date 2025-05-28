import asyncio
import json
import os
import uuid
from copy import deepcopy
from unittest import mock
from unittest.mock import Mock, AsyncMock

import pytest

from src.lambda_function import get_user_data_from_event, get_settings, add_user_spotify_data_to_queue, main
from src.models import User, Settings, UserSpotifyData, TimeRange, TopArtist, TopArtistsData, TopTrack, TopTracksData, \
    TopGenre, TopGenresData, TopEmotion, TopEmotionsData


# 1. Test get_settings raises KeyError if any settings missing from environment.
# 2. Test get_settings raises ValueError if request timeout cannot be parsed as float.
# 3. Test get_settings returns expected settings.

# 4. Test get_user_data_from_event raises KeyError if any fields missing from event.
# 5. Test get_user_data_from_event raises json.decoder.JSONDecodeError if body not valid JSON string.
# 6. Test get_user_data_from_event returns expected user.

# 7. Test add_user_spotify_data_to_queue calls sqs.send_message with expected params.

# 8. Test main calls expected methods with expected params.
# 9. Test main closes async client if exception occurs.


# 1. Test get_settings raises KeyError if any settings missing from environment.
@pytest.mark.parametrize("missing_setting", ["DATA_API_BASE_URL", "REQUEST_TIMEOUT", "QUEUE_URL"])
def test_get_settings_raises_key_error_if_any_settings_missing_from_environment(monkeypatch, missing_setting):
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "DATA_API_BASE_URL": "DATA_API_BASE_URL",
            "REQUEST_TIMEOUT": "10.0",
            "QUEUE_URL": "QUEUE_URL"
        }
        envvars.pop(missing_setting)
        for key, value in envvars.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(KeyError) as e:
            get_settings()

        assert missing_setting in str(e.value)


# 2. Test get_settings raises ValueError if request timeout cannot be parsed as float.
def test_get_settings_raises_value_error_if_request_timeout_cannot_be_parsed_as_float(monkeypatch):
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "DATA_API_BASE_URL": "DATA_API_BASE_URL",
            "REQUEST_TIMEOUT": "not a float",
            "QUEUE_URL": "QUEUE_URL"
        }
        for key, value in envvars.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(ValueError) as e:
            get_settings()

        assert "not a float" in str(e.value)


# 3. Test get_settings returns expected settings.
def test_get_settings_returns_expected_settings(monkeypatch):
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "DATA_API_BASE_URL": "DATA_API_BASE_URL",
            "REQUEST_TIMEOUT": "10.0",
            "QUEUE_URL": "QUEUE_URL"
        }
        for key, value in envvars.items():
            monkeypatch.setenv(key, value)

        settings = get_settings()

        expected_settings = Settings(data_api_base_url="DATA_API_BASE_URL", request_timeout=10.0, queue_url="QUEUE_URL")
        assert settings == expected_settings


def delete_field(data: dict, field: str):
    data_copy = deepcopy(data)
    keys = field.split(".")
    current = data_copy

    for key in keys[:-1]:
        if key == "[]":
            current = current[0]
        else:
            current = current[key]

    del current[keys[-1]]
    return data_copy, keys[-1]


@pytest.fixture
def mock_event():
    return {"Records": [{"body": {"user_id": "123", "refresh_token": "abc"}}]}


def convert_body_to_json_string(event: dict):
    records = event.get("Records")

    if isinstance(records, list):
        record = records[0]

        if "body" in record:
            record["body"] = json.dumps(record["body"])


# 4. Test get_user_data_from_event raises KeyError if any fields missing from event.
@pytest.mark.parametrize(
    "missing_field",
    [
        "Records",
        "Records.[].body",
        "Records.[].body.user_id",
        "Records.[].body.refresh_token"
    ]
)
def test_get_user_data_from_event_raises_key_error_if_any_fields_missing_from_event(mock_event, missing_field):
    test_event, deleted_field = delete_field(data=mock_event, field=missing_field)
    convert_body_to_json_string(test_event)

    with pytest.raises(KeyError) as e:
        get_user_data_from_event(test_event)

    assert deleted_field in str(e.value)


# 5. Test get_user_data_from_event raises json.decoder.JSONDecodeError if body not valid JSON string.
def test_get_user_data_from_event_raises_error_if_body_not_valid_json_string(mock_event):
    mock_event["Records"][0]["body"] = "hello"

    with pytest.raises(json.decoder.JSONDecodeError):
        get_user_data_from_event(mock_event)


# 6. Test get_user_data_from_event returns expected user.
def test_get_user_data_from_event_returns_expected_user(mock_event):
    convert_body_to_json_string(mock_event)

    user = get_user_data_from_event(mock_event)

    assert user == User(id="123", refresh_token="abc")


# 7. Test add_user_spotify_data_to_queue calls sqs.send_message with expected params.
def test_add_user_spotify_data_to_queue_calls_sqs_send_message_with_expected_params():
    mock_sqs = Mock()
    mock_user_spotify_data = UserSpotifyData(
        refresh_token="refresh",
        top_artists_data=[
            TopArtistsData(
                top_artists=[TopArtist(id="1", position=1), TopArtist(id="2", position=2)],
                time_range=TimeRange.SHORT
            ),
            TopArtistsData(
                top_artists=[TopArtist(id="1", position=1), TopArtist(id="2", position=2)],
                time_range=TimeRange.MEDIUM
            ),
            TopArtistsData(
                top_artists=[TopArtist(id="1", position=1), TopArtist(id="2", position=2)],
                time_range=TimeRange.LONG
            )
        ],
        top_tracks_data=[
            TopTracksData(
                top_tracks=[TopTrack(id="1", position=1), TopTrack(id="2", position=2)],
                time_range=TimeRange.SHORT
            ),
            TopTracksData(
                top_tracks=[TopTrack(id="1", position=1), TopTrack(id="2", position=2)],
                time_range=TimeRange.MEDIUM
            ),
            TopTracksData(
                top_tracks=[TopTrack(id="1", position=1), TopTrack(id="2", position=2)],
                time_range=TimeRange.LONG
            )
        ],
        top_genres_data=[
            TopGenresData(
                top_genres=[TopGenre(name="genre1", count=3), TopGenre(name="genre2", count=1)],
                time_range=TimeRange.SHORT
            ),
            TopGenresData(
                top_genres=[TopGenre(name="genre1", count=3), TopGenre(name="genre2", count=1)],
                time_range=TimeRange.MEDIUM
            ),
            TopGenresData(
                top_genres=[TopGenre(name="genre1", count=3), TopGenre(name="genre2", count=1)],
                time_range=TimeRange.LONG
            )
        ],
        top_emotions_data=[
            TopEmotionsData(
                top_emotions=[
                    TopEmotion(
                        name="emotion1",
                        percentage=0.3,
                        track_id="1"
                    ),
                    TopEmotion(
                        name="emotion2",
                        percentage=0.1,
                        track_id="2"
                    )
                ],
                time_range=TimeRange.SHORT
            ),
            TopEmotionsData(
                top_emotions=[
                    TopEmotion(
                        name="emotion1",
                        percentage=0.3,
                        track_id="1"
                    ),
                    TopEmotion(
                        name="emotion2",
                        percentage=0.1,
                        track_id="2"
                    )
                ],
                time_range=TimeRange.MEDIUM
            ),
            TopEmotionsData(
                top_emotions=[
                    TopEmotion(
                        name="emotion1",
                        percentage=0.3,
                        track_id="1"
                    ),
                    TopEmotion(
                        name="emotion2",
                        percentage=0.1,
                        track_id="2"
                    )
                ],
                time_range=TimeRange.LONG
            )
        ]
    )

    add_user_spotify_data_to_queue(sqs=mock_sqs, queue_url="url", user_id="1", user_spotify_data=mock_user_spotify_data)

    expected_message_data = {
        "user_id": "1",
        "refresh_token": "refresh",
        "top_artists_data": [
            {
                "top_artists": [{"id": "1", "position": 1}, {"id": "2", "position": 2}],
                "time_range": "short_term"
            },
            {
                "top_artists": [{"id": "1", "position": 1}, {"id": "2", "position": 2}],
                "time_range": "medium_term"
            },
            {
                "top_artists": [{"id": "1", "position": 1}, {"id": "2", "position": 2}],
                "time_range": "long_term"
            }
        ],
        "top_tracks_data": [
            {
                "top_tracks": [{"id": "1", "position": 1}, {"id": "2", "position": 2}],
                "time_range": "short_term"
            },
            {
                "top_tracks": [{"id": "1", "position": 1}, {"id": "2", "position": 2}],
                "time_range": "medium_term"
            },
            {
                "top_tracks": [{"id": "1", "position": 1}, {"id": "2", "position": 2}],
                "time_range": "long_term"
            }
        ],
        "top_genres_data": [
            {
                "top_genres": [{"name": "genre1", "count": 3}, {"name": "genre2", "count": 1}],
                "time_range": "short_term"
            },
            {
                "top_genres": [{"name": "genre1", "count": 3}, {"name": "genre2", "count": 1}],
                "time_range": "medium_term"
            },
            {
                "top_genres": [{"name": "genre1", "count": 3}, {"name": "genre2", "count": 1}],
                "time_range": "long_term"
            }
        ],
        "top_emotions_data": [
            {
                "top_emotions": [
                    {"name": "emotion1", "percentage": 0.3, "track_id": "1"},
                    {"name": "emotion2", "percentage": 0.1, "track_id": "2"}
                ],
                "time_range": "short_term"
            },
            {
                "top_emotions": [
                    {"name": "emotion1", "percentage": 0.3, "track_id": "1"},
                    {"name": "emotion2", "percentage": 0.1, "track_id": "2"}
                ],
                "time_range": "medium_term"
            },
            {
                "top_emotions": [
                    {"name": "emotion1", "percentage": 0.3, "track_id": "1"},
                    {"name": "emotion2", "percentage": 0.1, "track_id": "2"}
                ],
                "time_range": "long_term"
            }
        ]
    }
    mock_sqs.send_message.assert_called_once_with(
        QueueUrl="url",
        MessageBody=json.dumps(expected_message_data)
    )


# 8. Test main calls expected methods with expected params.
def test_main_calls_expected_methods_with_expected_params(mocker):
    mock_get_settings = mocker.patch(
        "src.lambda_function.get_settings",
        return_value=Settings(
            data_api_base_url="data_url",
            request_timeout=10.0,
            queue_url="queue_url"
        )
    )
    mock_get_user_data_from_event = mocker.patch(
        "src.lambda_function.get_user_data_from_event",
        return_value=User(id="1", refresh_token="refresh")
    )
    mock_client = Mock()
    mock_client_aclose = AsyncMock()
    mock_client.aclose = mock_client_aclose
    mock_async_client_class = mocker.patch("src.lambda_function.httpx.AsyncClient", return_value=mock_client)
    mock_data_service = Mock()
    mock_data_service.get_user_spotify_data = AsyncMock()
    mock_data_service.get_user_spotify_data.return_value = UserSpotifyData(
        refresh_token="new_refresh",
        top_artists_data=[],
        top_tracks_data=[],
        top_genres_data=[],
        top_emotions_data=[]
    )
    mock_data_service_class = mocker.patch("src.lambda_function.DataService", return_value=mock_data_service)
    mock_add_user_spotify_data_to_queue = mocker.patch("src.lambda_function.add_user_spotify_data_to_queue")
    mock_sqs = Mock()
    mocker.patch("src.lambda_function.boto3.client", return_value=mock_sqs)

    asyncio.run(main({}))

    mock_get_settings.assert_called_once()
    mock_get_user_data_from_event.assert_called_once_with({})
    mock_async_client_class.assert_called_once()
    mock_data_service_class.assert_called_once_with(
        client=mock_client,
        data_api_base_url="data_url",
        request_timeout=10.0
    )
    mock_data_service.get_user_spotify_data.assert_called_once_with("refresh")
    mock_add_user_spotify_data_to_queue.assert_called_once_with(
        sqs=mock_sqs,
        queue_url="queue_url",
        user_id="1",
        user_spotify_data=UserSpotifyData(
            refresh_token="new_refresh",
            top_artists_data=[],
            top_tracks_data=[],
            top_genres_data=[],
            top_emotions_data=[]
        )
    )
    mock_client_aclose.assert_called_once()


# 9. Test main closes async client if exception occurs.
def test_main_closes_async_client_if_exception_occurs(mocker):
    mocker.patch(
        "src.lambda_function.get_settings",
        return_value=Settings(
            data_api_base_url="data_url",
            request_timeout=10.0,
            queue_url="queue_url"
        )
    )
    mocker.patch(
        "src.lambda_function.get_user_data_from_event",
        return_value=User(id="1", refresh_token="refresh")
    )
    mock_client = Mock()
    mock_client_aclose = AsyncMock()
    mock_client.aclose = mock_client_aclose
    mocker.patch("src.lambda_function.httpx.AsyncClient", return_value=mock_client)
    mocker.patch("src.lambda_function.DataService", side_effect=Exception("test"))

    with pytest.raises(Exception):
        asyncio.run(main({}))

    mock_client_aclose.assert_called_once()
