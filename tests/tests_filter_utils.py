from unittest.mock import AsyncMock

import pytest

from filter_utils import filter_ips_input, filter_ips_list, filter_by_octet, shorten_ips
from messages import msg
from states import UserState

@pytest.mark.parametrize(
    "first_list, filter_type, expected_result, expected_state",
    [
        ("192.168.1.1\n192.168.1.2",
         'filter_by_list',
         msg['filter_ips_second'],
         UserState.AWAITING_FILTER_LIST_SECOND),

        ("192.168.1\n192.168.2",
         'filter_by_list',
         msg['filter_ips_second'],
         UserState.AWAITING_FILTER_LIST_SECOND),

        ("192.168.1 192.168.2 192.177.77",
         'filter_by_list',
         msg['filter_ips_second'],
         UserState.AWAITING_FILTER_LIST_SECOND),

        ("192.168.1.0 192.168.2.0 192.177.77.0",
         'filter_by_list',
         msg['filter_ips_second'],
         UserState.AWAITING_FILTER_LIST_SECOND),

        ("192.168.1 192.168.2.0 192.177.77.0 0.0.0.0..\n1.2.2.2 1.2.4.6 6.6.6 22.22.22\n\n\n123.123.123.22",
         'filter_by_list',
         msg['filter_ips_second'],
         UserState.AWAITING_FILTER_LIST_SECOND),

        ("192.168 192\n\n\n1112.1412512",
         'filter_by_list',
         msg['no_ips'],
         UserState.AWAITING_FILTER_LIST_FIRST),

        ("тест, раз, два, три",
         'filter_by_list',
         msg['no_ips'],
         UserState.AWAITING_FILTER_LIST_FIRST),

        ("",
         'filter_by_list',
         msg['no_ips'],
         UserState.AWAITING_FILTER_LIST_FIRST),

        ("192.168.1.1\n192.168.1.2",
         'filter_by_octet',
         msg['enter_octet'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("192.168.1\n192.168.2",
         'filter_by_octet',
         msg['enter_octet'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("192.168.1 192.168.2 192.177.77",
         'filter_by_octet',
         msg['enter_octet'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("192.168.1.0 192.168.2.0 192.177.77.0",
         'filter_by_octet',
         msg['enter_octet'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("192.168.1 192.168.2.0 192.177.77.0 0.0.0.0..\n1.2.2.2 1.2.4.6 6.6.6 22.22.22\n\n\n123.123.123.22",
         'filter_by_octet',
         msg['enter_octet'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("192.168 192\n\n\n1112.1412512",
         'filter_by_octet',
         msg['no_ips'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("тест, раз, два, три",
         'filter_by_octet',
         msg['no_ips'],
         UserState.AWAITING_FILTER_OCTET_SECOND),

        ("",
         'filter_by_octet',
         msg['no_ips'],
         UserState.AWAITING_FILTER_LIST_FIRST),

        ("192.168.1.1\n192.168.2.2",
         'remove_fourth_octet',
         "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.2</code>",
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("192.168.6.6 192.168.10.11",
         'remove_fourth_octet',
         "Обработанные IP-адреса:\n<code>192.168.6</code>\n<code>192.168.10</code>",
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("192.168.1.6\n192.168.26.6\n192.177.77.11",
         'remove_fourth_octet',
         "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.26</code>\n<code>192.177.77</code>",
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("192.168.1.0 192.168.2.0 192.177.77.0",
         'remove_fourth_octet',
         "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.2</code>\n<code>192.177.77</code>",
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("192.168.1.100 192.168.2.0 192.177.77.0 0.0.0.0..\n1.2.2.2 1.2.4.6 6.6.6.10 22.22.22.100\n\n\n123.123.123.22",
         'remove_fourth_octet',
         "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.2</code>\n<code>192.177.77</code>\n<code>0.0.0</code>\n"
         "<code>1.2.2</code>\n<code>1.2.4</code>\n<code>6.6.6</code>\n<code>22.22.22</code>\n<code>123.123.123</code>",
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("192.168 192\n\n\n11.12.14.125.12",
         'remove_fourth_octet',
         "Обработанные IP-адреса:\n<code>11.12.14</code>",
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("тест, раз, два, три",
         'remove_fourth_octet',
         msg['no_ips'],
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("",
         'remove_fourth_octet',
         msg['no_ips'],
         UserState.AWAITING_FILTER_REMOVE_FOURTH_OCTET_LIST),

        ("192.168.1.1:2000\n192.168.2.2:1000",
         'remove_port',
         "Обработанные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.2.2</code>",
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("192.168.6.6:1111 192.168.10.11:2222",
         'remove_port',
         "Обработанные IP-адреса:\n<code>192.168.6.6</code>\n<code>192.168.10.11</code>",
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("192.168.1.6:1233\n192.168.26.6:5000\n192.177.77.11:5555",
         'remove_port',
         "Обработанные IP-адреса:\n<code>192.168.1.6</code>\n<code>192.168.26.6</code>\n<code>192.177.77.11</code>",
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("192.168.1.0:0000 192.168.2.0:2233 192.177.77.0:4455",
         'remove_port',
         "Обработанные IP-адреса:\n<code>192.168.1.0</code>\n<code>192.168.2.0</code>\n<code>192.177.77.0</code>",
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("192.168.1.100:5555 192.168.2.0:6666 192.177.77.0:0009 0.0.0.0:1233..\n1.2.2.2:3311 1.2.4.6:5000 6.6.6.10:9090 22.22.22.100:0000\n\n\n123.123.123.22:9999",
         'remove_port',
         "Обработанные IP-адреса:\n<code>192.168.1.100</code>\n<code>192.168.2.0</code>\n<code>192.177.77.0</code>\n<code>0.0.0.0</code>\n"
         "<code>1.2.2.2</code>\n<code>1.2.4.6</code>\n<code>6.6.6.10</code>\n<code>22.22.22.100</code>\n<code>123.123.123.22</code>",
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("192.168:0000 192\n\n\n11.12.14.125:1233",
         'remove_port',
         "Обработанные IP-адреса:\n<code>11.12.14.125</code>",
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("тест, раз, два, три",
         'remove_port',
         msg['no_ips'],
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST),

        ("",
         'remove_port',
         msg['no_ips'],
         UserState.AWAITING_FILTER_REMOVE_PORT_LIST)
    ]
)
@pytest.mark.asyncio
async def test_filter_ips_input(first_list, filter_type, expected_result, expected_state):
    """Тестирование функции filter_ips_input с разными входными данными"""
    # мок состояние пользователя
    mock_state = AsyncMock()

    # устанавливаем что состояние пользователя равно expected_state
    mock_state.get_state.return_value = expected_state
    mock_state.get_data.return_value = {'first_list': first_list}

    # выполняем функцию
    result = await filter_ips_input(first_list, filter_type, mock_state)

    # проверяем результат выполнения функции
    assert result == expected_result

    # проверяем состояние пользователя после выполнения функции
    assert await mock_state.get_state() == expected_state

    # проверяем содержимое get_data
    if result is not msg['no_ips']:
        mock_state.update_data.assert_awaited_with(first_list=first_list)

@pytest.mark.parametrize(
    "first_list, second_list, expected_result, expected_state",
    [
        ("192.168.1.1\n192.168.1.2", "192.168.1.3\n192.168.1.4", "Отфильтрованные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.1.2</code>", UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.1\n192.168.2", "192.168.3\n192.168.4", "Отфильтрованные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.2</code>", UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.1\n192.168.2\n192.168.1.1", "192.168.1\n192.168.4", "Отфильтрованные IP-адреса:\n<code>192.168.2</code>\n<code>192.168.1.1</code>", UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.1 192.168.2 192.168.1.1", "192.168.1 192.168.4", "Отфильтрованные IP-адреса:\n<code>192.168.2</code>\n<code>192.168.1.1</code>", UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.115.116.1 192.168.2.115.116 192.168.1.1.25.26", "192.168.115.116", "Отфильтрованные IP-адреса:\n<code>192.168.2.115</code>\n<code>192.168.1.1</code>", UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.1.1\n192.168.1.2", "192.168.1.1\n192.168.1.2", msg['no_filtered_ips'], UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.1.10\n192.168.1.12", "192.168.1", "Отфильтрованные IP-адреса:\n<code>192.168.1.10</code>\n<code>192.168.1.12</code>", UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168\n1.2\n9.1", "9.1\n192.168", msg["no_ips_second"], UserState.AWAITING_FILTER_LIST_FIRST),
        ("192.168.1.1\n192.168.1.2", "Тест, раз, два, три", msg["no_ips_second"], UserState.AWAITING_FILTER_LIST_SECOND),
    ]
)
@pytest.mark.asyncio
async def test_filter_ips_list(first_list, second_list, expected_result, expected_state):
    """Тестирование функции filter_ips_list с разными входными данными (проверка результата функции и состояния пользователя)"""
    # мок состояние пользователя
    mock_state = AsyncMock()

    # присваиваем first_list состоянию get_data
    mock_state.get_data.return_value = {"first_list": first_list}

    # устанавливаем что состояние пользователя равно expected_state
    mock_state.get_state.return_value = expected_state

    # выполняем функцию
    result = await filter_ips_list(second_list, mock_state)

    # проверяем результат выполнения функции
    assert result == expected_result

    # проверяем состояние пользователя после выполнения функции
    assert await mock_state.get_state() == expected_state

@pytest.mark.parametrize(
    "first_list, target_octet, expected_result, expected_state",
    [
        ("192.168.1.1\n192.168.1.2\n12.12.15.17\n66.66.66.66", "192", "Отфильтрованные IP-адреса:\n<code>12.12.15.17</code>\n<code>66.66.66.66</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.5\n192.168.10\n1.1.1.1\n2.2.2.2.", "192", "Отфильтрованные IP-адреса:\n<code>1.1.1.1</code>\n<code>2.2.2.2</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1 192.168.2.1 192.168.1.3 99.99.99.100 99.10.25.666", "99",
        "Отфильтрованные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.2.1</code>\n<code>192.168.1.3</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.5\n192.168.10\n1.1.1\n2.2.2", "192", "Отфильтрованные IP-адреса:\n<code>1.1.1</code>\n<code>2.2.2</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.115 16.17.3.5 27.52.78.2 2.2.2.2 1.1.1.1.1..\n192.168.2.115.116 1.12.25.26", "192",
         "Отфильтрованные IP-адреса:\n<code>16.17.3.5</code>\n<code>27.52.78.2</code>\n<code>2.2.2.2</code>\n<code>1.1.1.1</code>\n<code>1.12.25.26</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1\n192.168.1.2\n27.52.78.2 2.2.2.2 7.7.7.7", "1",
         "Отфильтрованные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.1.2</code>\n<code>27.52.78.2</code>\n<code>2.2.2.2</code>\n<code>7.7.7.7</code>",
         UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1\n192.168.1.2\n192.52.78.2 192.2.2.2 192.7.7.7", "192", msg['no_filtered_ips'], UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1\n192.168.1.2", "1000", msg['invalid_octet'], UserState.AWAITING_FILTER_OCTET_SECOND),
        ("192.168.1.1\n192.168.1.2", "Невалидный октет", msg['invalid_octet'], UserState.AWAITING_FILTER_OCTET_SECOND),
    ]
)
@pytest.mark.asyncio
async def test_filter_by_octet(first_list, target_octet, expected_result, expected_state):
    """Тестирование функции filter_by_octet с разными входными данными (проверка результата функции и состояния пользователя)"""
    # мок состояние пользователя
    mock_state = AsyncMock()

    # устанавливаем ожидаемое состояние пользователя после выполнения функции
    mock_state.get_state.return_value = expected_state

    # устанавливаем список для фильтрации
    mock_state.get_data.return_value = {"first_list": first_list}

    # выполняем функцию
    result = await filter_by_octet(target_octet, mock_state)

    # проверяем результат выполнения функции
    assert result == expected_result

    # проверяем состояние пользователя после выполнения функции
    assert await mock_state.get_state() == expected_state

@pytest.mark.parametrize(
    "first_list, octet_flag, expected_result, expected_state",
    [
        ("192.168.1.1\n192.168.1.2", True,
        "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.1</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.5\n192.168.10\n1.1.1.1", True,
        "Обработанные IP-адреса:\n<code>192.168.5</code>\n<code>192.168.10</code>\n<code>1.1.1</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1 192.168.2.1 192.168.1.3", True,
        "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.2</code>\n<code>192.168.1</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.115 16.17.3.5 27.52.78.2 2.2.2.2 1.1.1.1.1..\n192.168.2.115.116 1.12.25.26", True,
        "Обработанные IP-адреса:\n<code>192.168.115</code>\n<code>16.17.3</code>\n<code>27.52.78</code>\n<code>2.2.2</code>\n"
        "<code>1.1.1</code>\n<code>192.168.2</code>\n<code>1.12.25</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1\n192.168.1.2\n27.52.78.2 2.2.2.2 7.7.7.7", True,
        "Обработанные IP-адреса:\n<code>192.168.1</code>\n<code>192.168.1</code>\n<code>27.52.78</code>\n<code>2.2.2</code>\n<code>7.7.7</code>",
         UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1:100000\n192.168.1.2:2000", False,
        "Обработанные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.1.2</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.5:2200\n192.168.10:2422\n1.1.1.1:222", False,
        "Обработанные IP-адреса:\n<code>192.168.5</code>\n<code>192.168.10</code>\n<code>1.1.1.1</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1:3333 192.168.2.1:2111 192.168.1.3:1111", False,
        "Обработанные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.2.1</code>\n<code>192.168.1.3</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.115:1110 16.17.3.5:2777 27.52.78.2:7744 2.2.2.2:2374 1.1.1.1.1:333dsa..\n192.168.2.115:4323 1.12.25.26:6162", False,
        "Обработанные IP-адреса:\n<code>192.168.115</code>\n<code>16.17.3.5</code>\n<code>27.52.78.2</code>\n<code>2.2.2.2</code>\n"
        "<code>1.1.1.1</code>\n<code>192.168.2.115</code>\n<code>1.12.25.26</code>", UserState.AWAITING_FILTER_OCTET_FIRST),
        ("192.168.1.1:22222\n192.168.1.2:222233\n27.52.78.2:5122 2.2.2.2 7.7.7.7:64323", False,
        "Обработанные IP-адреса:\n<code>192.168.1.1</code>\n<code>192.168.1.2</code>\n<code>27.52.78.2</code>\n<code>2.2.2.2</code>\n<code>7.7.7.7</code>",
         UserState.AWAITING_FILTER_OCTET_FIRST)
    ]
)
@pytest.mark.asyncio
async def test_shorten_ips(first_list, octet_flag, expected_result, expected_state):
    """Тестирование функции filter_by_octet с разными входными данными (проверка результата функции и состояния пользователя)"""
    # мок состояние пользователя
    mock_state = AsyncMock()

    # устанавливаем ожидаемое состояние пользователя после выполнения функции
    mock_state.get_state.return_value = expected_state

    # устанавливаем список для фильтрации
    mock_state.get_data.return_value = {"first_list": first_list}

    # выполняем функцию
    result = await shorten_ips(octet_flag, mock_state)

    # проверяем результат выполнения функции
    assert result == expected_result

    # проверяем состояние пользователя после выполнения функции
    assert await mock_state.get_state() == expected_state