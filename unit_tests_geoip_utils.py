import pytest
from unittest.mock import MagicMock
from geoip_utils import add_cities, make_cities_dict, get_ip_info_result

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
    """Тестирование функции add_cities с разными входными данными"""
    # выполняем функцию
    await get_ip_info_result(new_text_dict, result)

    # проверяем результат выполнения функции
    assert result == expected_result