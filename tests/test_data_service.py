from unittest.mock import Mock, AsyncMock, call

import httpx
import pytest

from src.models import Tokens, ItemType, TimeRange, UserSpotifyData, TopArtistsData, TopTracksData, TopGenresData, \
    TopEmotionsData, TopArtist, TopTrack, TopGenre, TopEmotion
from src.data_service import DataService, DataServiceException

# 1. Test _get_data_from_api raises DataServiceException if httpx.HTTPStatusError occurs.
# 2. Test _get_data_from_api raises DataServiceException if httpx.RequestError occurs.
# 3. Test _get_data_from_api calls client.post with expected params.

# 4. Test _refresh_tokens raises DataServiceException if no access token returned by API.
# 5. Test _refresh_tokens returns expected tokens.

# 6. Test _create_top_items_data raises DataServiceException if item_type invalid.
# 7. Test _create_top_items_data raises DataServiceException if missing field.
# 8. Test _create_top_items_data returns expected top items data.

# 9. Test _get_top_items_data calls expected methods with expected params.

# 10. Test _get_all_top_items calls expected methods with expected params.

# 11. Test get_user_spotify_data calls expected methods with expected params.
# 12. Test get_user_spotify_data returns expected user spotify data.


@pytest.fixture
def mock_post_request() -> Mock:
    mock_req = AsyncMock()
    return mock_req


@pytest.fixture
def mock_response(mock_post_request) -> Mock:
    mock_res = Mock()
    mock_res.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="",
        request=mock_post_request,
        response=mock_res
    )
    return mock_res


@pytest.fixture
def mock_client() -> Mock:
    mock_clt = Mock()
    return mock_clt


@pytest.fixture
def data_service(mock_client) -> DataService:
    return DataService(client=mock_client, data_api_base_url="http://test-url.com", request_timeout=10.0)


# 1. Test _get_data_from_api raises DataServiceException if httpx.HTTPStatusError occurs.
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, expected_error_message",
    [(401, "Unauthorised API request"), (500, "Unsuccessful API request")]
)
async def test__get_data_from_api_raises_data_service_exception_if_http_status_error_occurs(
        data_service,
        mock_client,
        mock_post_request,
        mock_response,
        status_code,
        expected_error_message
):
    mock_response.status_code = status_code
    mock_post_request.return_value = mock_response
    mock_client.post = mock_post_request

    with pytest.raises(DataServiceException) as e:
        await data_service._get_data_from_api(url="", json_data={})

    assert expected_error_message in str(e.value)


# 2. Test _get_data_from_api raises DataServiceException if httpx.RequestError occurs.
@pytest.mark.asyncio
async def test__get_data_from_api_raises_spotify_service_exception_if_request_error_occurs(
        data_service,
        mock_client,
        mock_post_request
):
    mock_post_request.side_effect = httpx.RequestError(message="")
    mock_client.post = mock_post_request

    with pytest.raises(DataServiceException) as e:
        await data_service._get_data_from_api(url="", json_data={})

    assert "Failed to make API request" in str(e.value)


# 3. Test _get_data_from_api calls client.post with expected params.
@pytest.mark.asyncio
async def test__get_data_from_api_calls_client_post_with_expected_params(
        data_service,
        mock_client,
        mock_post_request
):
    mock_post_request.return_value = Mock()
    mock_client.post = mock_post_request

    await data_service._get_data_from_api(url="url", json_data={"key": "value"})

    mock_post_request.assert_called_once_with(url="url", params=None, json={"key": "value"}, timeout=10.0)


@pytest.fixture
def mock_token_data_factory():
    def _create(access_token: str | None = None, refresh_token: str | None = None) -> dict[str, str]:
        mock_token_data = {}

        if access_token is not None:
            mock_token_data["access_token"] = access_token

        if refresh_token is not None:
            mock_token_data["refresh_token"] = refresh_token

        return mock_token_data

    return _create


@pytest.fixture
def mock__get_data_from_api() -> AsyncMock:
    mock = AsyncMock()
    return mock


# 4. Test _refresh_tokens raises DataServiceException if no access token returned by API.
@pytest.mark.asyncio
async def test__refresh_tokens_raises_spotify_service_exception_if_access_token_not_present_in_api_response(
        data_service,
        mock__get_data_from_api,
        mock_token_data_factory
):
    mock_token_data = mock_token_data_factory(refresh_token="def")
    mock__get_data_from_api.return_value = mock_token_data
    data_service._get_data_from_api = mock__get_data_from_api

    with pytest.raises(DataServiceException) as e:
        await data_service._refresh_tokens(refresh_token="abc")

    assert "No access_token present in API response" in str(e.value)


# 5. Test _refresh_tokens returns expected tokens.
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "access_token, refresh_token",
    [("abc", "def"), ("abc", None)]
)
async def test__refresh_tokens_returns_expected_tokens(
        data_service,
        mock__get_data_from_api,
        mock_token_data_factory,
        access_token,
        refresh_token
):
    mock_token_data = mock_token_data_factory(access_token=access_token, refresh_token=refresh_token)
    mock__get_data_from_api.return_value = mock_token_data
    data_service._get_data_from_api = mock__get_data_from_api

    token_data = await data_service._refresh_tokens(refresh_token="ghi")

    assert token_data == Tokens(access_token=access_token, refresh_token=refresh_token)


# 6. Test _create_top_items_data raises DataServiceException if item_type invalid.
def test__create_top_items_data_raises_data_service_exception_if_item_type_invalid(data_service):
    with pytest.raises(DataServiceException, match="Invalid item type"):
        data_service._create_top_items_data(data=[], item_type="", time_range=TimeRange.SHORT)


# 7. Test _create_top_items_data raises DataServiceException if missing field.
@pytest.mark.parametrize(
    "item_type, data, missing_field",
    [
        (ItemType.ARTIST, [{}], "id"),
        (ItemType.TRACK, [{}], "id"),
        (ItemType.GENRE, [{"count": 1}], "name"),
        (ItemType.GENRE, [{"name": "test"}], "count"),
        (ItemType.EMOTION, [{"percentage": 0.2}], "name"),
        (ItemType.EMOTION, [{"name": "test"}], "percentage")
    ]
)
def test__create_top_items_data_raises_data_service_exception_if_missing_artist_or_track_id(
        data_service,
        item_type,
        data,
        missing_field
):
    with pytest.raises(DataServiceException, match="Missing field in API data") as e:
        data_service._create_top_items_data(data=data, item_type=item_type, time_range=TimeRange.SHORT)

    assert missing_field in str(e.value)


# 8. Test _create_top_items_data returns expected top items data.
@pytest.mark.parametrize(
    "item_type, data, expected_output",
    [
        (
                ItemType.ARTIST,
                [{"id": "1"}, {"id": "2"}],
                TopArtistsData(
                    top_artists=[TopArtist(id="1", position=1), TopArtist(id="2", position=2)],
                    time_range=TimeRange.SHORT
                )
        ),
        (
                ItemType.TRACK,
                [{"id": "1"}, {"id": "2"}],
                TopTracksData(
                    top_tracks=[TopTrack(id="1", position=1), TopTrack(id="2", position=2)],
                    time_range=TimeRange.SHORT
                )
        ),
        (
                ItemType.GENRE,
                [{"name": "genre1", "count": 3}, {"name": "genre2", "count": 1}],
                TopGenresData(
                    top_genres=[TopGenre(name="genre1", count=3), TopGenre(name="genre2", count=1)],
                    time_range=TimeRange.SHORT
                )
        ),
        (
                ItemType.EMOTION,
                [{"name": "emotion1", "percentage": 0.3}, {"name": "emotion2", "percentage": 0.1}],
                TopEmotionsData(
                    top_emotions=[
                        TopEmotion(name="emotion1", percentage=0.3),
                        TopEmotion(name="emotion2", percentage=0.1)
                    ],
                    time_range=TimeRange.SHORT
                )
        )
    ]
)
def test__create_top_items_data_returns_expected_top_items_data(data_service, item_type, data, expected_output):
    top_items_data = data_service._create_top_items_data(data=data, item_type=item_type, time_range=TimeRange.SHORT)

    assert top_items_data == expected_output


# 9. Test _get_top_items_data calls expected methods with expected params.
@pytest.mark.asyncio
async def test__get_top_items_data_calls_expected_methods_with_expected_params(
        data_service,
        mock__get_data_from_api
):
    mock__get_data_from_api.return_value = []
    data_service._get_data_from_api = mock__get_data_from_api
    mock__create_top_items_data = Mock()
    data_service._create_top_items_data = mock__create_top_items_data

    await data_service._get_top_items_data(access_token="access", item_type=ItemType.ARTIST, time_range=TimeRange.SHORT)

    mock__get_data_from_api.assert_called_once_with(
        url="http://test-url.com/data/me/top/artists",
        json_data={"access_token": "access"},
        params={"time_range": "short_term"}
    )
    mock__create_top_items_data.assert_called_once_with(data=[], item_type=ItemType.ARTIST, time_range=TimeRange.SHORT)


# 10. Test _get_all_top_items calls expected methods with expected params.
@pytest.mark.asyncio
async def test__get_all_top_items_calls_expected_methods_with_expected_params(data_service):
    mock__get_top_items_data = AsyncMock()
    data_service._get_top_items_data = mock__get_top_items_data

    await data_service._get_all_top_items(access_token="access", item_type=ItemType.TRACK)

    expected_calls = [
        call(access_token="access", item_type=ItemType.TRACK, time_range=TimeRange.SHORT),
        call(access_token="access", item_type=ItemType.TRACK, time_range=TimeRange.MEDIUM),
        call(access_token="access", item_type=ItemType.TRACK, time_range=TimeRange.LONG)
    ]
    mock__get_top_items_data.assert_has_calls(expected_calls, any_order=False)
    assert mock__get_top_items_data.call_count == 3


# 11. Test get_user_spotify_data calls expected methods with expected params.


# 12. Test get_user_spotify_data returns expected user spotify data.


# @pytest.fixture
# def mock_top_items_data() -> dict:
#     return {
#         "items": [
#             {"id": "1"},
#             {"id": "2"},
#             {"id": "3"},
#             {"id": "4"},
#             {"id": "5"},
#         ]
#     }
#
#
# @pytest.mark.asyncio
# async def test__get_top_items_raises_spotify_service_exception_if_no_items_key_in_data(
#         mock_spotify_service,
#         mock__make_request,
#         mock_top_items_data
# ):
#     mock_top_items_data.pop("items")
#     mock__make_request.return_value = mock_top_items_data
#     mock_spotify_service._make_request = mock__make_request
#
#     with pytest.raises(DataServiceException) as e:
#         await mock_spotify_service._get_top_items(access_token="", item_type=ItemType.TRACK, time_range=TimeRange.SHORT)
#
#     assert "API response data in unexpected format" in str(e.value)
#
#
# @pytest.mark.asyncio
# async def test__get_top_items_raises_spotify_service_exception_if_no_id_field_for_one_item(
#         mock_spotify_service,
#         mock__make_request,
#         mock_top_items_data
# ):
#     mock_top_items_data["items"][0].pop("id")
#     mock__make_request.return_value = mock_top_items_data
#     mock_spotify_service._make_request = mock__make_request
#
#     with pytest.raises(DataServiceException) as e:
#         await mock_spotify_service._get_top_items(access_token="", item_type=ItemType.TRACK, time_range=TimeRange.SHORT)
#
#     assert "API response data in unexpected format" in str(e.value)
#
#
# @pytest.mark.asyncio
# async def test__get_top_items_raises_spotify_service_exception_if_items_list_is_empty(
#         mock_spotify_service,
#         mock__make_request,
#         mock_top_items_data
# ):
#     mock_top_items_data["items"] = []
#     mock__make_request.return_value = mock_top_items_data
#     mock_spotify_service._make_request = mock__make_request
#
#     with pytest.raises(DataServiceException) as e:
#         await mock_spotify_service._get_top_items(access_token="", item_type=ItemType.TRACK, time_range=TimeRange.SHORT)
#
#     assert "No top items found" in str(e.value)
#
#
# @pytest.mark.asyncio
# async def test__get_top_items_returns_expected_top_items_data(
#         mock_spotify_service,
#         mock__make_request,
#         mock_top_items_data
# ):
#     mock__make_request.return_value = mock_top_items_data
#     mock_spotify_service._make_request = mock__make_request
#
#     top_items_data = await mock_spotify_service._get_top_items(
#         access_token="",
#         item_type=ItemType.TRACK,
#         time_range=TimeRange.SHORT
#     )
#
#     expected_top_items_data = TopItemsData(
#         top_items=[
#             TopItem(id="1", position=1),
#             TopItem(id="2", position=2),
#             TopItem(id="3", position=3),
#             TopItem(id="4", position=4),
#             TopItem(id="5", position=5)
#         ],
#         time_range=TimeRange.SHORT
#     )
#     assert top_items_data == expected_top_items_data
#
#
# @pytest.mark.asyncio
# async def test__get_all_top_items_raises_exception_if_any_tasks_fail(mock_spotify_service):
#     mock__get_top_items = AsyncMock()
#     mock__get_top_items.side_effect = DataServiceException("test")
#     mock_spotify_service._get_top_items = mock__get_top_items
#
#     with pytest.raises(DataServiceException) as e:
#         await mock_spotify_service._get_all_top_items(access_token="", item_type=ItemType.TRACK)
#
#     assert "test" in str(e.value)
#
#
# @pytest.mark.asyncio
# async def test__get_all_top_items_returns_expected_data(
#         mock_spotify_service,
#         mock__make_request,
#         mock_top_items_data
# ):
#     mock__make_request.return_value = mock_top_items_data
#     mock_spotify_service._make_request = mock__make_request
#
#     all_top_items = await mock_spotify_service._get_all_top_items(access_token="", item_type=ItemType.TRACK)
#
#     expected_all_top_items = [
#         TopItemsData(
#             top_items=[
#                 TopItem(id="1", position=1),
#                 TopItem(id="2", position=2),
#                 TopItem(id="3", position=3),
#                 TopItem(id="4", position=4),
#                 TopItem(id="5", position=5)
#             ],
#             time_range=TimeRange.SHORT
#         ),
#         TopItemsData(
#             top_items=[
#                 TopItem(id="1", position=1),
#                 TopItem(id="2", position=2),
#                 TopItem(id="3", position=3),
#                 TopItem(id="4", position=4),
#                 TopItem(id="5", position=5)
#             ],
#             time_range=TimeRange.MEDIUM
#         ),
#         TopItemsData(
#             top_items=[
#                 TopItem(id="1", position=1),
#                 TopItem(id="2", position=2),
#                 TopItem(id="3", position=3),
#                 TopItem(id="4", position=4),
#                 TopItem(id="5", position=5)
#             ],
#             time_range=TimeRange.LONG
#         )
#     ]
#     assert all_top_items == expected_all_top_items
#
#
# @pytest.fixture
# def mock_all_top_items_data() -> list[TopItemsData]:
#     return [
#         TopItemsData(
#             top_items=[
#                 TopItem(id="1", position=1),
#                 TopItem(id="2", position=2),
#                 TopItem(id="3", position=3),
#                 TopItem(id="4", position=4),
#                 TopItem(id="5", position=5)
#             ],
#             time_range=TimeRange.SHORT
#         ),
#         TopItemsData(
#             top_items=[
#                 TopItem(id="1", position=1),
#                 TopItem(id="2", position=2),
#                 TopItem(id="3", position=3),
#                 TopItem(id="4", position=4),
#                 TopItem(id="5", position=5)
#             ],
#             time_range=TimeRange.MEDIUM
#         ),
#         TopItemsData(
#             top_items=[
#                 TopItem(id="1", position=1),
#                 TopItem(id="2", position=2),
#                 TopItem(id="3", position=3),
#                 TopItem(id="4", position=4),
#                 TopItem(id="5", position=5)
#             ],
#             time_range=TimeRange.LONG
#         )
#     ]
#
#
# @pytest.mark.asyncio
# async def test_get_user_spotify_data_returns_expected_spotify_user_data(
#         mock_spotify_service,
#         mock_all_top_items_data
# ):
#     mock__refresh_tokens = AsyncMock()
#     mock__refresh_tokens.return_value = Tokens(access_token="abc", refresh_token="def")
#     mock_spotify_service._refresh_tokens = mock__refresh_tokens
#     mock__get_all_top_items = AsyncMock()
#     mock__get_all_top_items.return_value = mock_all_top_items_data
#     mock_spotify_service._get_all_top_items = mock__get_all_top_items
#
#     user_spotify_data = await mock_spotify_service.get_user_spotify_data(refresh_token="")
#
#     expected_user_spotify_data = UserSpotifyData(
#         refresh_token="def",
#         top_artists_data=mock_all_top_items_data,
#         top_tracks_data=mock_all_top_items_data
#     )
#     assert user_spotify_data == expected_user_spotify_data
