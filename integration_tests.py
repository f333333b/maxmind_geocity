import pytest
from unittest.mock import AsyncMock, patch

from geoip_utils import process_check

# is_update_needed
# process_check
# get_ip_info
# make_cities_dict

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_state_key, user_id, target_flag, mock_result, expected_answer",
    [
        (
                'awaiting_target_check',
                '1',
                False,
                '''
                Сервер №36 (35 прокси, 5 подсетей):
                171.22.76. - 12 прокси
                102.129.221. - 7 прокси
                181.214.117. - 6 прокси
                Сервер №188 (30 прокси, 2 подсетей):
                195.96.157. - 18 прокси
                Сервер №193 (9 прокси, 1 подсетей):
                '''
                ,
                '''
                🇺🇸 US (США)
                Джэксонвилл
                171.22.76. - 12 прокси
                Вашингтон
                102.129.221. - 7 прокси
            
                🇦🇪 AE (ОАЭ)
                Абу-Даби
                181.214.117. - 6 прокси
            
                🇸🇨 SC (Сейшельские о-ва)
                Виктория
                195.96.157. - 18 прокси
                '''
        ),
        (
                'awaiting_target_check',
                '1',
                True,
                '123',
                'Во введенном тексте IP-адреса не найдены.'
        )
    ])
async def test_process_check(user_state_key, user_id, target_flag, mock_result, expected_answer):
    message = AsyncMock()
    message.text = '''  
    Сервер №36 (35 прокси, 5 подсетей):
    171.22.76. - 12 прокси
    102.129.221. - 7 прокси
    181.214.117. - 6 прокси
    Сервер №188 (30 прокси, 2 подсетей):
    195.96.157. - 18 прокси
    Сервер №193 (9 прокси, 1 подсетей):'''
    result_copy = None
    with patch('main_func.get_ip_info', new=AsyncMock(return_value=(mock_result, result_copy))):
        await process_check(user_state_key, message, user_id, target_flag)
        message.answer.assert_awaited_once_with(
            expected_answer,
            parse_mode="HTML",
            reply_markup=None
        )
