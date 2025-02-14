import pytest
from unittest.mock import MagicMock, patch

import db_capitals_utils

@pytest.mark.asyncio
async def test_init_db_pool():
    mock_pool = MagicMock()  # Создаём мок для пула соединений
    with patch("asyncpg.create_pool", return_value=mock_pool):  # Мокаем создание пула
        await db_capitals_utils.init_db_pool()
        assert db_capitals_utils.db_pool is mock_pool  # Проверяем, что db_pool был правильно установлен