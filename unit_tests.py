import pytest
from asynctest import CoroutineMock, patch, MagicMock
from db_updating import download_database
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.asyncio
async def test_download_database():
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"test data")
    mock_get_context = MagicMock()
    mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_context.__aexit__ = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.get.return_value = mock_get_context
    with patch("aiohttp.ClientSession", return_value=mock_session) as mock_client:
        await download_database()
        mock_session.get.assert_called_once()

#скачивание через http
#сохранение на диск
#распаковка
#перемещение в нужную папку
#удаление временных файлов
#обработка ошибок

# download_database - наличие файла в папке с определенной датой?
# process_target_output
# add_cities
# filter_ips_input
# filter_ips_list
# filter_by_octet