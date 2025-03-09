import asyncio
import aiohttp
import asyncpg
import countryflag
import json

from db_capitals_utils import get_db_pool

async def check_status(id):
    url = f'https://check-host.net/check-result/{id}'
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            print(json.dumps(data, indent=4, ensure_ascii=False))
            return data

async def ping_proxy(ip: str):
    """Функция проверки прокси"""
    ip_numbers = 10
    headers = {'Accept': 'application/json'}
    full_url = f'https://check-host.net/check-ping?host={ip}&max_nodes={ip_numbers}'
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=headers) as response:
            data = await response.json()
            print(json.dumps(data, indent=4, ensure_ascii=False))
            request_id = data['request_id']
            await asyncio.sleep(5)
            check_status_result = await check_status(request_id)
            formatted_result = await format_ping_results(check_status_result)
            #print(formatted_result)
            return formatted_result

async def format_ping_results(check_status_result):
    """Форматирует результаты ping для вывода в Telegram"""
    db_pool = await get_db_pool()
    result = ["📡 Результаты проверки:", ""]
    for node, pings in check_status_result.items():
        if not pings:
            result.append("⚠ Нет данных о пинге для этого узла.")
            continue

        print(f'node={node}')
        print(f'pings={pings}')
        #if not pings or pings[0]:
        #    continue
        async with db_pool.acquire() as conn:
            country_result = await conn.fetchrow(
                """
                SELECT country FROM capitals
                WHERE ISO = $1
                """, node[0:2].upper())
            if country_result:
                country_name = country_result['country']
            else:
                country_name = "Неизвестно"

        iso_code = node[:2].upper() if len(node) >= 2 else "XX"
        result.append(f"{countryflag.getflag([iso_code])} {country_name}")

        for ping_group in pings:
            for ping in ping_group:
                status = ping[0]
                latency = ping[1]
                print(f'latency={latency}')
                ip = ping[2] if len(ping) > 2 else "Неизвестно"

                latency = latency[0] if isinstance(latency, list) else latency
                latency_str = f"{latency:.3f} мс" if isinstance(latency, (int, float)) else "Неизвестно"

                ping_result = "❌" if status != "OK" else f'✅ Пинг {latency_str}'

                result.append(ping_result)
        result.append("")
    #print("\n".join(result))
    return "\n".join(result)

async def main():
    """Функция проверки конкретного URL для отладки"""
    await ping_proxy("google.com")

if __name__ == "__main__":
    asyncio.run(main())
