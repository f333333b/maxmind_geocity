import pytest
from states import UserState
from config import pattern
from asynctest import CoroutineMock, patch, MagicMock
from db_updating import download_database
from unittest.mock import MagicMock, AsyncMock, patch
from aiogram.fsm.context import FSMContext
from filter_utils import filter_ips_list

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

@pytest.mark.parametrize(
    "second_list, first_list, expected_result", [
        # Пример 1: Есть несколько IP в first_list, но они не совпадают с second_list
        (["192.168.1.1", "192.168.1.2"], ["192.168.1.3", "192.168.1.4"], "Отфильтрованные IP-адреса:\n<code>192.168.1.3</code>\n<code>192.168.1.4</code>"),

        # Пример 2: Все IP в first_list есть в second_list
        (["192.168.1.1", "192.168.1.2"], ["192.168.1.1", "192.168.1.2"], "Нет отфильтрованных IP-адресов."),

        # Пример 3: second_list не содержит валидных IP-адресов
        (["Некорректный текст"], ["192.168.1.1", "192.168.1.2"], "Список IP не найден."),

        # Пример 4: Пустой second_list
        ([], ["192.168.1.1", "192.168.1.2"], "Отфильтрованные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.1.2</code>"),
    ]
)
@pytest.mark.asyncio
async def test_filter_ips_list(second_list, first_list, expected_result):
    """Тестирование функции filter_ips_list с разными входными данными"""

    # Создаем мок состояния FSM
    mock_state = MagicMock()

    # Настроим данные пользователя (user_data) с ключом user_id
    user_data = {1: {'first': ', '.join(first_list)}}  # user_id = 1, первый список
    user_id = 1  # в данном примере это всегда 1

    # Вызываем функцию
    result = await filter_ips_list(second_list, user_id, mock_state)

    # Проверяем результат
    assert result == expected_result
    mock_state.set_state.assert_called_once_with(UserState.AWAITING_FILTER_LIST_FIRST)

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