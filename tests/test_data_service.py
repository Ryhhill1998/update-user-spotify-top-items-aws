from unittest.mock import Mock, AsyncMock

import httpx
import pytest

from src.models import Tokens, ItemType, TimeRange, UserSpotifyData
from src.data_service import DataService, DataServiceException

# 1. Test _get_data_from_api raises DataServiceException if httpx.HTTPStatusError occurs.
# 2. Test _get_data_from_api raises DataServiceException if httpx.RequestError occurs.
# 3. Test _get_data_from_api calls client.post with expected params.
# 4. Test _refresh_tokens raises DataServiceException if no access token returned by API.
# 5. Test _refresh_tokens returns expected tokens.
# 6. Test _create_top_items_data raises DataServiceException if item_type invalid.
# 7. Test _create_top_items_data raises DataServiceException if missing artist ID.
# 8. Test _create_top_items_data raises DataServiceException if missing track ID.
# 9. Test _create_top_items_data raises DataServiceException if missing genre name.
# 10. Test _create_top_items_data raises DataServiceException if missing genre count.
# 11. Test _create_top_items_data raises DataServiceException if missing emotion name.
# 12. Test _create_top_items_data raises DataServiceException if missing emotion percentage.
# 13. Test _create_top_items_data returns expected top artists data.
# 14. Test _create_top_items_data returns expected top tracks data.
# 15. Test _create_top_items_data returns expected top genres data.
# 16. Test _create_top_items_data returns expected top emotions data.
# 17. Test _get_top_items_data calls expected methods with expected params.
# 18. Test _get_all_top_items calls expected methods with expected params.
# 19. Test get_user_spotify_data calls expected methods with expected params.
# 20. Test get_user_spotify_data returns expected user spotify data.


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
def mock_spotify_service(mock_client) -> DataService:
    return DataService(client=mock_client, data_api_base_url="", request_timeout=10.0)


# 1. Test _get_data_from_api raises DataServiceException if httpx.HTTPStatusError occurs.
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, expected_error_message",
    [(401, "Unauthorised API request"), (500, "Unsuccessful API request")]
)
async def test__get_data_from_api_raises_data_service_exception_if_http_status_error_occurs(
        mock_spotify_service,
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
        await mock_spotify_service._get_data_from_api(url="", json_data={})

    assert expected_error_message in str(e.value)


# 2. Test _get_data_from_api raises DataServiceException if httpx.RequestError occurs.
@pytest.mark.asyncio
async def test__get_data_from_api_raises_spotify_service_exception_if_request_error_occurs(
        mock_spotify_service,
        mock_client,
        mock_post_request
):
    mock_post_request.side_effect = httpx.RequestError(message="")
    mock_client.post = mock_post_request

    with pytest.raises(DataServiceException) as e:
        await mock_spotify_service._get_data_from_api(url="", json_data={})

    assert "Failed to make API request" in str(e.value)


# 3. Test _get_data_from_api calls client.post with expected params.
@pytest.mark.asyncio
async def test__get_data_from_api_raises_spotify_service_exception_if_request_error_occurs(
        mock_spotify_service,
        mock_client,
        mock_post_request
):
    mock_client.post = mock_post_request

    await mock_spotify_service._get_data_from_api(url="url", json_data={"key": "value"})

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
        mock_spotify_service,
        mock__get_data_from_api,
        mock_token_data_factory
):
    mock_token_data = mock_token_data_factory(refresh_token="def")
    mock__get_data_from_api.return_value = mock_token_data
    mock_spotify_service._get_data_from_api = mock__get_data_from_api

    with pytest.raises(DataServiceException) as e:
        await mock_spotify_service._refresh_tokens(refresh_token="abc")

    assert "No access_token present in API response" in str(e.value)


# 5. Test _refresh_tokens returns expected tokens.
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "access_token, refresh_token",
    [("abc", "def"), ("abc", None)]
)
async def test__refresh_tokens_returns_expected_tokens(
        mock_spotify_service,
        mock__get_data_from_api,
        mock_token_data_factory,
        access_token,
        refresh_token
):
    mock_token_data = mock_token_data_factory(access_token=access_token, refresh_token=refresh_token)
    mock__get_data_from_api.return_value = mock_token_data
    mock_spotify_service._get_data_from_api = mock__get_data_from_api

    token_data = await mock_spotify_service._refresh_tokens(refresh_token="ghi")

    assert token_data == Tokens(access_token=access_token, refresh_token=refresh_token)


# 6. Test _create_top_items_data raises DataServiceException if item_type invalid.
# 7. Test _create_top_items_data raises DataServiceException if missing artist ID.
# 8. Test _create_top_items_data raises DataServiceException if missing track ID.
# 9. Test _create_top_items_data raises DataServiceException if missing genre name.
# 10. Test _create_top_items_data raises DataServiceException if missing genre count.
# 11. Test _create_top_items_data raises DataServiceException if missing emotion name.
# 12. Test _create_top_items_data raises DataServiceException if missing emotion percentage.
# 13. Test _create_top_items_data returns expected top artists data.
# 14. Test _create_top_items_data returns expected top tracks data.
# 15. Test _create_top_items_data returns expected top genres data.
# 16. Test _create_top_items_data returns expected top emotions data.


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
