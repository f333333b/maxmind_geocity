import pytest
from unittest.mock import AsyncMock, patch
from filter_utils import filter_by_octet

# download_database - наличие файла в папке с определенной датой?
# process_target_output
# add_cities
# filter_ips_input
# filter_ips_list
# filter_by_octet

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_data.get(user_id, [])=123.123.123.123, user_id",
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
async def test_process_target_output(result_copy):
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
