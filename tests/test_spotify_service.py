from unittest.mock import Mock, AsyncMock

import httpx
import pytest

from src.models import Tokens, ItemType, TimeRange, TopItem, TopItemsData
from src.spotify_service import SpotifyService, SpotifyServiceException


@pytest.fixture
def mock_request() -> Mock:
    mock_req = AsyncMock()
    return mock_req


@pytest.fixture
def mock_response(mock_request) -> Mock:
    mock_res = Mock()
    mock_res.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="",
        request=mock_request,
        response=mock_res
    )
    return mock_res


@pytest.fixture
def mock_client() -> Mock:
    mock_clt = Mock()
    return mock_clt


@pytest.fixture
def mock_spotify_service(mock_client) -> SpotifyService:
    return SpotifyService(client=mock_client, client_id="", client_secret="", auth_url="", data_base_url="")


@pytest.mark.asyncio
async def test__make_request_raises_spotify_service_exception_if_unauthorised_response(
        mock_spotify_service,
        mock_client,
        mock_request,
        mock_response
):
    mock_response.status_code = 401
    mock_request.return_value = mock_response
    mock_client.request = mock_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._make_request(method="", url="")

    assert "Unauthorised API request" in str(e.value)


@pytest.mark.asyncio
async def test__make_request_raises_spotify_service_exception_if_other_non_success_response(
        mock_spotify_service,
        mock_client,
        mock_request,
        mock_response
):
    mock_response.status_code = 500
    mock_request.return_value = mock_response
    mock_client.request = mock_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._make_request(method="", url="")

    assert "Unsuccessful API request" in str(e.value)


@pytest.mark.asyncio
async def test__make_request_raises_spotify_service_exception_if_request_fails(
        mock_spotify_service,
        mock_client,
        mock_request
):
    mock_request.side_effect = httpx.RequestError(message="")
    mock_client.request = mock_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._make_request(method="", url="")

    assert "Failed to make API request" in str(e.value)


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
def mock__make_request() -> AsyncMock:
    mock = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test__refresh_tokens_raises_spotify_service_exception_if_access_token_not_present_in_api_response(
        mock_spotify_service,
        mock__make_request,
        mock_token_data_factory
):
    mock_token_data = mock_token_data_factory(refresh_token="def")
    mock__make_request.return_value = mock_token_data
    mock_spotify_service._make_request = mock__make_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._refresh_tokens(refresh_token="abc")

    assert "No access_token present in API response" in str(e.value)


@pytest.mark.asyncio
async def test__refresh_tokens_returns_none_for_refresh_token_if_missing_from_api_response(
        mock_spotify_service,
        mock__make_request,
        mock_token_data_factory
):
    mock_token_data = mock_token_data_factory(access_token="def")
    mock__make_request.return_value = mock_token_data
    mock_spotify_service._make_request = mock__make_request

    token_data = await mock_spotify_service._refresh_tokens(refresh_token="abc")

    assert token_data == Tokens(access_token="def", refresh_token=None)


@pytest.mark.asyncio
async def test__refresh_tokens_returns_both_tokens_if_present_in_api_response(
        mock_spotify_service,
        mock__make_request,
        mock_token_data_factory
):
    mock_token_data = mock_token_data_factory(access_token="def", refresh_token="ghi")
    mock__make_request.return_value = mock_token_data
    mock_spotify_service._make_request = mock__make_request

    token_data = await mock_spotify_service._refresh_tokens(refresh_token="abc")

    assert token_data == Tokens(access_token="def", refresh_token="ghi")


@pytest.fixture
def mock_top_items_data() -> dict:
    return {
        "items": [
            {"id": "1"},
            {"id": "2"},
            {"id": "3"},
            {"id": "4"},
            {"id": "5"},
        ]
    }


@pytest.mark.asyncio
async def test__get_top_items_raises_spotify_service_exception_if_no_items_key_in_data(
        mock_spotify_service,
        mock__make_request,
        mock_top_items_data
):
    mock_top_items_data.pop("items")
    mock__make_request.return_value = mock_top_items_data
    mock_spotify_service._make_request = mock__make_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._get_top_items(access_token="", item_type=ItemType.TRACK, time_range=TimeRange.SHORT)

    assert "API response data in unexpected format" in str(e.value)


@pytest.mark.asyncio
async def test__get_top_items_raises_spotify_service_exception_if_no_id_field_for_one_item(
        mock_spotify_service,
        mock__make_request,
        mock_top_items_data
):
    mock_top_items_data["items"][0].pop("id")
    mock__make_request.return_value = mock_top_items_data
    mock_spotify_service._make_request = mock__make_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._get_top_items(access_token="", item_type=ItemType.TRACK, time_range=TimeRange.SHORT)

    assert "API response data in unexpected format" in str(e.value)


@pytest.mark.asyncio
async def test__get_top_items_raises_spotify_service_exception_if_items_list_is_empty(
        mock_spotify_service,
        mock__make_request,
        mock_top_items_data
):
    mock_top_items_data["items"] = []
    mock__make_request.return_value = mock_top_items_data
    mock_spotify_service._make_request = mock__make_request

    with pytest.raises(SpotifyServiceException) as e:
        await mock_spotify_service._get_top_items(access_token="", item_type=ItemType.TRACK, time_range=TimeRange.SHORT)

    assert "No top items found" in str(e.value)


@pytest.mark.asyncio
async def test__get_top_items_returns_expected_top_items_data(
        mock_spotify_service,
        mock__make_request,
        mock_top_items_data
):
    mock__make_request.return_value = mock_top_items_data
    mock_spotify_service._make_request = mock__make_request

    top_items_data = await mock_spotify_service._get_top_items(
        access_token="",
        item_type=ItemType.TRACK,
        time_range=TimeRange.SHORT
    )

    expected_top_items_data = TopItemsData(
        top_items=[
            TopItem(id="1", position=1),
            TopItem(id="2", position=2),
            TopItem(id="3", position=3),
            TopItem(id="4", position=4),
            TopItem(id="5", position=5)
        ],
        time_range=TimeRange.SHORT
    )
    assert top_items_data == expected_top_items_data


@pytest.mark.asyncio
async def test__get_all_top_items():
    pass


@pytest.mark.asyncio
async def test_get_user_spotify_data():
    pass
