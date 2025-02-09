import pytest
from db_updating import download_database
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_download_database():
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"test data")
    mock_get_context = AsyncMock()
    mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_context.__aexit__ = AsyncMock(return_value=None)
    mock_session = AsyncMock()
    mock_session.get.return_value = mock_get_context
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await download_database()
        mock_session.get.assert_called_once()