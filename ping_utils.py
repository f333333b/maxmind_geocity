import asyncio
import aiohttp
from aiohttp import BasicAuth

async def check_url(url: str):
    proxies = {
        'Латвия': ('http://185.122.206.243:4656', BasicAuth('user149714', '50lkae')),
        'Россия': (None, None),
        'Финляндия': ('http://109.196.106.122:2120', BasicAuth('user184781', 'h7er2u'))
    }
    max_length = max(len(country) + (len(proxy[0]) if proxy[0] else 0) for country, proxy in proxies.items())
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for country, (proxy_url, proxy_auth) in proxies.items():
            if proxy_url and proxy_auth:
                task = asyncio.create_task(session.get(url, proxy=proxy_url, proxy_auth=proxy_auth, timeout=aiohttp.ClientTimeout(total=2)))
            else:
                task = asyncio.create_task(session.get(url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=2)))
            tasks.append((country, task))
            try:
                async with session.get('https://api.ipify.org', proxy=proxy_url, proxy_auth=proxy_auth if proxy_auth else None) as ip_response:
                    response = await task
                    ip = await ip_response.text()
                    results[f'{country} ({ip})'] = '✅' if response.status == 200 else f'❌ (Status: {response.status})'
            except Exception as e:
                results[country] = f'❌ ({str(e)})'
    for country, status in results.items():
        print(f"{country:<{max_length}}{status}")

async def main():
    await check_url('https://Pornhub.ru')

if __name__ == "__main__":
    asyncio.run(main())