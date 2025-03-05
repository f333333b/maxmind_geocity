import asyncio
import aiohttp

async def check_status(id):
    url = f'https://check-host.net/check-result/{id}'
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data

async def ping_proxy(ip: str):
    """Функция проверки прокси"""
    ip_numbers = 10
    headers = {'Accept': 'application/json'}
    full_url = f'https://check-host.net/check-ping?host={ip}&max_nodes={ip_numbers}'
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=headers) as response:
            data = await response.json()
            request_id = data['request_id']
            await asyncio.sleep(10)
            check_status_result = await check_status(request_id)
            formatted_result = await format_ping_results(check_status_result)
            #print(formatted_result)
            return formatted_result

async def format_ping_results(check_status_result):
    """Форматирует результаты ping для вывода в Telegram"""
    result = ["📡 Результаты проверки:", ""]
    for node, pings in check_status_result.items():
        print(node, pings)
        result.append(f"🌍 *{node}*")
        for i, ping in enumerate(pings[0]):
            status, latency = ping[0], ping[1]
            ip = ping[2] if len(ping) > 2 else None
            emoji = "✅" if status == "OK" else "❌"
            if ip and i == 0:
                result.append(f"   ├ {emoji} `{ip}` — *{latency:.2f} ms*")
            else:
                prefix = "   └" if i == len(pings[0]) - 1 else "   ├"
                result.append(f"   {prefix} {emoji} *{latency:.2f} ms*")
        result.append("")
    #print("\n".join(result))
    return "\n".join(result)

async def main():
    """Функция проверки конкретного URL для отладки"""
    await ping_proxy("google.com")

if __name__ == "__main__":
    asyncio.run(main())
