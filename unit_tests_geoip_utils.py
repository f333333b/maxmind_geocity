import pytest
from unittest.mock import MagicMock, AsyncMock
from geoip_utils import add_cities, make_cities_dict, get_ip_info_result, get_ip_info

@pytest.mark.parametrize(
    "new_text_dict, result_copy, line, match, country_id, city, target_flag, expected_new_text_dict, expected_result_copy",
    [
        (
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {}}},
            [],
            '91.124.18. - 107 прокси',
            '91.124.18',
            'UA',
            'Киев',
            False,
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>91.124.18</code>. - 107 прокси']}}},
            []
        ),
        ({'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {}}},
            [],
            '89.251.31.3 - 87 прокси',
            '89.251.31.3',
            'UA',
            'Киев',
            False,
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>89.251.31.3</code> - 87 прокси']}}},
            []
        )
    ]
)
@pytest.mark.asyncio
async def test_add_cities(new_text_dict, result_copy, line, match, country_id, city, target_flag, expected_new_text_dict, expected_result_copy):
    """Тестирование функции add_cities с разными входными данными"""
    # выполняем функцию
    await add_cities(new_text_dict, result_copy, line, match, country_id, city, target_flag)

    # проверяем результат выполнения функции
    assert new_text_dict == expected_new_text_dict
    assert result_copy == expected_result_copy

@pytest.mark.parametrize(
    "match, city_response, new_text_dict, target_flag, target_country_iso, result_copy, line, expected_new_text_dict",
    [
        # стандартный случай, валидный IP-адрес, new_text_dict пуст
        (
            '123.123.123.123',
            {"iso_code": "CN", "country_ru": "Китай", "city_ru": "Пекин"},
            {},
            False,
            None,
            [],
            '123.123.123.123',
            {'CN': {'head': '\n🇨🇳 CN (Китай)', 'cities': {'Пекин': ['<code>123.123.123.123</code>']}}}
        ),
        # стандартный случай, валидный IP-адрес, в new_text_dict один IP-адрес
        (
            '3.3.3.3',
            {"iso_code": "US", "country_ru": "США", "city_ru": "Ашберн"},
            {'CN': {'head': '\n🇨🇳 CN (Китай)', 'cities': {'Пекин': ['<code>123.123.123.123</code>']}}},
            False,
            None,
            [],
            '3.3.3.3',
            {'CN': {'head': '\n🇨🇳 CN (Китай)', 'cities': {'Пекин': ['<code>123.123.123.123</code>']}}, 'US': {'head': '\n🇺🇸 US (США)', 'cities': {'Ашберн': ['<code>3.3.3.3</code>']}}}
        ),
        # невалидный IP-адрес
        (
            '1.1.1.1',
            {"iso_code": "Unknown", "country_ru": "Unknown", "city_ru": "Unknown"},
            {},
            False,
            None,
            [],
            '1.1.1.1',
            {'Unknown': {'cities': {'\n❌Invalid IP': ['<b><code>1.1.1.1</code></b>']}}}
        ),
        # в new_text_dict есть IP-адрес того же города
        (
            '91.124.1',
            {"iso_code": "GB", "country_ru": "Британия", "city_ru": "Лондон"},
            {'GB': {'head': '\n🇬🇧 GB (Британия)', 'cities': {'Лондон': ['<code>91.124.19</code>']}}},
            False,
            None,
            [],
            '91.124.1',
            {'GB': {'head': '\n🇬🇧 GB (Британия)', 'cities': {'Лондон': ['<code>91.124.19</code>', '<code>91.124.1</code>']}}},
        ),
        # в new_text_dict есть тот же IP-адрес
        (
            '91.124.19',
            {"iso_code": "GB", "country_ru": "Британия", "city_ru": "Лондон"},
            {'GB': {'head': '\n🇬🇧 GB (Британия)', 'cities': {'Лондон': ['<code>91.124.19</code>']}}},
            False,
            None,
            [],
            '91.124.19',
            {'GB': {'head': '\n🇬🇧 GB (Британия)', 'cities': {'Лондон': ['<code>91.124.19</code>']}}},
        ),
        # в new_text_dict есть IP-адрес той же страны другого города
        (
            '62.204.52',
            {"iso_code": "UA", "country_ru": "Украина", "city_ru": "Харьков"},
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>62.233.60</code>. - 74 прокси']}}},
            False,
            None,
            [],
            '62.204.52. - 68 прокси',
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>62.233.60</code>. - 74 прокси'], 'Харьков': ['<code>62.204.52</code>. - 68 прокси']}}},
        ),
        # IP-адрес, город которого отсутствует в базе данных
        (
                '91.124.18',
                {"iso_code": "UA", "country_ru": "Украина", "city_ru": "Киев"},
                {},
                False,
                None,
                [],
                '91.124.18',
                {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>91.124.18</code>']}}}
        )
    ]
)
@pytest.mark.asyncio
async def test_make_cities_dict(match, city_response, new_text_dict, target_flag, target_country_iso, result_copy, line,
                                expected_new_text_dict):
    """Тестирование функции make_cities_dict с разными входными данными"""

    mock_city_file = MagicMock()

    mock_city_file.city.return_value = MagicMock(
        country=MagicMock(
            iso_code=city_response["iso_code"],
            names={
                "ru": city_response["country_ru"],
                "en": "Ukraine"  # добавляем ключ "en" с нужным значением
            }
        ),
        city=MagicMock(
            names={"ru": city_response["city_ru"]}
        )
    )

    # выполняем функцию
    await make_cities_dict(match, mock_city_file, new_text_dict, target_flag, target_country_iso, result_copy, line)

    # проверяем результат выполнения функции
    assert new_text_dict == expected_new_text_dict

@pytest.mark.parametrize(
    "new_text_dict, result, expected_result",
    [
        # один IP-адрес
        (
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>91.124.18</code>']}}},
            [],
            ['\n🇺🇦 UA (Украина)', 'Киев', '<code>91.124.18</code>']
        ),
        # несколько IP-адресов
        (
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>91.124.18</code>']}}, 'GB': {'head': '\n🇬🇧 GB (Британия)',
            'cities': {'Сербитон': ['<code>91.125.55</code>']}}, 'Unknown': {'cities': {'\n❌Invalid IP': ['<b><code>1.1.1.1</code></b>']}},
             'US': {'head': '\n🇺🇸 US (США)', 'cities': {'Ашберн': ['<code>3.3.3.3</code>']}}},
            [],
            ['\n🇺🇦 UA (Украина)', 'Киев', '<code>91.124.18</code>', '\n🇬🇧 GB (Британия)', 'Сербитон', '<code>91.125.55</code>',
            '\n❌Invalid IP', '<b><code>1.1.1.1</code></b>', '\n🇺🇸 US (США)', 'Ашберн', '<code>3.3.3.3</code>']
        ),
        (
            {'UA': {'head': '\n🇺🇦 UA (Украина)', 'cities': {'Киев': ['<code>91.124.18</code> 91.125.55 1.1.1.1 3.3.3.3']}},
            'GB': {'head': '\n🇬🇧 GB (Британия)', 'cities': {'Сербитон': ['91.124.18 <code>91.125.55</code> 1.1.1.1 3.3.3.3']}},
             'Unknown': {'cities': {'\n❌Invalid IP': ['91.124.18 91.125.55 <b><code>1.1.1.1</code></b> 3.3.3.3']}},
             'US': {'head': '\n🇺🇸 US (США)', 'cities': {'Ашберн': ['91.124.18 91.125.55 1.1.1.1 <code>3.3.3.3</code>']}}},
            [],
            ['\n🇺🇦 UA (Украина)', 'Киев', '<code>91.124.18</code> 91.125.55 1.1.1.1 3.3.3.3', '\n🇬🇧 GB (Британия)', 'Сербитон',
             '91.124.18 <code>91.125.55</code> 1.1.1.1 3.3.3.3', '\n❌Invalid IP', '91.124.18 91.125.55 <b><code>1.1.1.1</code></b> 3.3.3.3',
             '\n🇺🇸 US (США)', 'Ашберн', '91.124.18 91.125.55 1.1.1.1 <code>3.3.3.3</code>']
        )
    ]
)
@pytest.mark.asyncio
async def test_get_ip_info_result(new_text_dict, result, expected_result):
    """Тестирование функции get_ip_info_result с разными входными данными"""
    # выполняем функцию
    await get_ip_info_result(new_text_dict, result)

    # проверяем результат выполнения функции
    assert result == expected_result

@pytest.mark.parametrize(
    "text_input, target_flag, expected_result, expected_result_copy",
    [
        # невалидный IP-адрес (2 октета)
        (
            "123.123",
            False,
            [],
            []
        ),
        # невалидный IP-адрес (текст)
        (
            "тестовый текст",
            False,
            [],
            []
        ),
        # один IP-адрес (4 октета), target_flag=False
        (
            "123.255.1.1",
            False,
            ['\n🇳🇿 NZ (Новая Зеландия)', 'Веллингтон', '<code>123.255.1.1</code>'],
            []
        ),
        # один IP-адрес (3 октета), target_flag=False
        (
            "123.255.1",
            False,
            ['\n🇳🇿 NZ (Новая Зеландия)', 'Веллингтон', '<code>123.255.1</code>'],
            []
        ),
        # один IP-адрес (4 октета), которого нет в базе данных, target_flag=False
        (
            "1.1.1.1",
            False,
            ['\n❌Invalid IP', '<b><code>1.1.1.1</code></b>'],
            []
        ),
        # несколько IP-адресов (4 октета) в столбик, target_flag=False
        (
            """
            123.255.1.1
            4.4.4.4
            3.3.3.3
            22.22.22.22
            """,
            False,
            ['\n🇳🇿 NZ (Новая Зеландия)', 'Веллингтон', '<code>123.255.1.1</code>', '\n🇺🇸 US (США)', 'Омаха',
             '<code>4.4.4.4</code>', 'Ашберн', '<code>3.3.3.3</code>', 'Вашингтон', '<code>22.22.22.22</code>'],
            []
        ),
        # несколько IP-адресов (4 октета) в столбик, target_flag=False
        (
            "123.255.1.1 4.4.4.4 3.3.3.3 22.22.22.22",
            False,
            ['\n🇳🇿 NZ (Новая Зеландия)', 'Веллингтон', '<code>123.255.1.1</code> 4.4.4.4 3.3.3.3 22.22.22.22',
             '\n🇺🇸 US (США)', 'Омаха', '123.255.1.1 <code>4.4.4.4</code> 3.3.3.3 22.22.22.22', 'Ашберн',
             '123.255.1.1 4.4.4.4 <code>3.3.3.3</code> 22.22.22.22', 'Вашингтон',
             '123.255.1.1 4.4.4.4 3.3.3.3 <code>22.22.22.22</code>'],
            []
        ),
        # несколько IP-адресов (3 и 4 октета) в строку, target_flag=False
        (
            "123.123.124.125 1.2.3.4 1.2.2 5.5.5",
            False,
            ['\n🇨🇳 CN (Китай)', 'Пекин', '<code>123.123.124.125</code> 1.2.3.4 1.2.2 5.5.5',
             '123.123.124.125 1.2.3.4 <code>1.2.2</code> 5.5.5', '\n🇦🇺 AU (Австралия)', 'Канберра',
             '123.123.124.125 <code>1.2.3.4</code> 1.2.2 5.5.5', '\n🇩🇪 DE (ФРГ)', 'Берлин',
             '123.123.124.125 1.2.3.4 1.2.2 <code>5.5.5</code>'],
            []
        ),
        # несколько IP-адресов (3 и 4 октета) в столбик, target_flag=False
        (
            """
            33.44.55.66
            78.78.78.78
            45.45.45
            90.90.90
            """,
            False,
            ['\n🇺🇸 US (США)', 'Вашингтон', '<code>33.44.55.66</code>', '\n🇸🇪 SE (Швеция)', 'Стокгольм',
             '<code>78.78.78.78</code>', '\n🇨🇦 CA (Канада)', 'Оттава', '<code>45.45.45</code>',
             '\n🇫🇷 FR (Франция)', 'Нёйи-сюр-Сен', '<code>90.90.90</code>'],
            []
        ),
        # несколько повторяющихся IP-адресов (3 и 4 октета), target_flag=False
        (
            """
            33.44.55.66
            33.44.55.66 33.22.44
            45.45.45 33.44.55
            90.90.90
            90.90.90.123
            """,
            False,
            ['\n🇺🇸 US (США)', 'Вашингтон', '<code>33.44.55.66</code>', '<code>33.44.55.66</code> 33.22.44',
              '33.44.55.66 <code>33.22.44</code>', '45.45.45 <code>33.44.55</code>', '\n🇨🇦 CA (Канада)', 'Оттава',
              '<code>45.45.45</code> 33.44.55', '\n🇫🇷 FR (Франция)', 'Нёйи-сюр-Сен', '<code>90.90.90</code>', '<code>90.90.90.123</code>'],
            []
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_ip_info(text_input, target_flag, expected_result, expected_result_copy):
    """Упрощённое тестирование функции get_ip_info с разными входными данными"""

    mock_get_capital = AsyncMock(return_value="Веллингтон")

    # Мокируем работу с geoip2 (функция make_cities_dict)
    mock_make_cities_dict = AsyncMock()

    # Мокируем подключение к базе данных (db_pool)
    mock_db_pool = MagicMock()
    mock_db_pool.acquire.return_value = AsyncMock()

    # Тестируем функцию get_ip_info
    result, result_copy = await get_ip_info(
        text_input=text_input,
        target_flag=target_flag,
        db_pool=mock_db_pool,  # Переопределяем db_pool
        get_capital=mock_get_capital,  # Переопределяем get_capital
        make_cities_dict=mock_make_cities_dict  # Переопределяем make_cities_dict
    )

    # Проверка результата
    assert result == expected_result
    assert result_copy == expected_result_copy

    # Проверяем вызовы моков
    #mock_db_pool.acquire.assert_called_once()
    #mock_get_capital.assert_called_once_with(
    #    'New Zealand')  # Проверяем, что функция get_capital была вызвана с нужным аргументом
    #mock_make_cities_dict.assert_called()  # Проверяем, что make_cities_dict был вызван хотя бы один раз