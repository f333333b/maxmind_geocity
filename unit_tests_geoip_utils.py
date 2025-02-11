import pytest
from geoip_utils import add_cities

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

