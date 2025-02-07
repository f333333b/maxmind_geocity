import pytest
from unittest.mock import MagicMock, AsyncMock
from db_capitals_utils import get_capital

@pytest.mark.asyncio
async def test_get_capital():
    """Юнит-тест функции get_capital()"""
    # создаем mock-пул к базе данных
    mock_db_pool = MagicMock()

    # создаем mock-подключение к базе данных
    mock_connection = AsyncMock()

    # связываем mock_db_pool и mock_connection
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection

    # указываем ответ при запросе в базу данных
    mock_connection.fetch.return_value = [{'capital': 'Москва'}]

    import db_capitals_utils

    db_capitals_utils.db_pool = mock_db_pool
    result = await get_capital('Russia')
    assert result == [{'capital': 'Москва'}]



# download_database - наличие файла в папке с определенной датой?
# process_target_output
# add_cities
# filter_ips_input
# filter_ips_list
# filter_by_octet