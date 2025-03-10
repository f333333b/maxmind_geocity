import asyncio
import aiohttp
import countryflag
import re

from config import pattern_ping
from db_capitals_utils import get_db_pool
from messages import msg

async def check_status(id):
    url = f'https://check-host.net/check-result/{id}'
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data

async def ping_proxy(ip: str):
    """Функция проверки прокси"""
    if not re.findall(pattern_ping, ip):
        return msg['invalid_proxy']
    node_ru = 'ru1.node.check-host.net'
    node_ua = 'ua1.node.check-host.net'
    node_us = 'us1.node.check-host.net'
    node_br = 'br1.node.check-host.net'
    node_il = 'il1.node.check-host.net'
    node_tr = 'tr1.node.check-host.net'
    node_nl = 'nl2.node.check-host.net'
    node_fi = 'fi1.node.check-host.net'
    node_de = 'de4.node.check-host.net'
    node_bg = 'bg1.node.check-host.net'
    headers = {'Accept': 'application/json'}
    full_url = (f'https://check-host.net/check-ping?host={ip}&node={node_ru}&node={node_ua}'
                f'&node={node_us}&node={node_br}&node={node_il}&node={node_tr}&node={node_nl}'
                f'&node={node_fi}&node={node_de}&node={node_bg}')
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=headers) as response:
            data = await response.json()
            request_id = data['request_id']
            await asyncio.sleep(5)
            check_status_result = await check_status(request_id)
            formatted_result = await format_ping_results(check_status_result)
            return formatted_result

async def get_country_name(db_pool, iso_code):
    async with db_pool.acquire() as conn:
        country_result = await conn.fetchrow(
            """
            SELECT country FROM capitals
            WHERE ISO = $1
            """, iso_code.upper())
        if country_result:
            return country_result['country']
        else:
            return "Неизвестно"

async def format_ping_results(check_status_result):
    """Форматирует результаты ping для вывода в Telegram"""
    db_pool = await get_db_pool()
    result = ["📡 Результаты проверки:", ""]
    for node, pings in check_status_result.items():
        country_name = await get_country_name(db_pool, node[0:2])
        iso_code = node[:2].upper() if len(node) >= 2 else "XX"
        result.append(f"{countryflag.getflag([iso_code])} {country_name}")
        if not pings:
            result.append("⚠ Нет данных о пинге для этого узла.")
            continue
        ping_results = []
        for ping_group in pings:
            for ping in ping_group:
                if not ping:
                    latency = '❌ Ошибка при попытке пинга'
                    ping_results.append(latency)
                else:
                    latency = ping[1]
                    latency = latency[0] if isinstance(latency, list) else latency
                    latency_str = float(f"{latency:.3f}") if isinstance(latency, (int, float)) else "Неизвестно"
                    ping_results.append(latency_str)
        if any(x == '❌ Ошибка при попытке пинга' for x in ping_results):
            for result_instance in ping_results:
                try:
                    latency_str = float(f"{result_instance:.3f}")
                    result.append(f'✅ Пинг: {latency_str} мс')
                except Exception as e:
                    result.append(result_instance)
        else:
            avg_ping_results = f'{(sum(ping_results) / len(ping_results)):.3f}' if ping_results else 0
            result.append(f'✅ Пинг: {str(avg_ping_results)} мс')
    sorted_result = await sort_result(result)
    return "\n".join(sorted_result)

async def sort_result(data):
    entries = [(data[i], data[i + 1]) for i in range(2, len(data) - 1, 2)]
    entries.sort(key=lambda x: (x[0] != '🇷🇺 Russia', x[0] != '🇺🇦 Ukraine'))
    result = [data[0], '']
    for country, ping in entries:
        result.append(country)
        result.append(f'{ping}\n')
    return result

async def main():
    """Функция проверки конкретного URL для отладки"""
    await ping_proxy("google.com")

if __name__ == "__main__":
    asyncio.run(main())