import asyncio
import aiohttp
from aiohttp import BasicAuth, ClientError, ClientConnectionError, ClientSSLError, ClientTimeout
from urllib.parse import urlparse
import requests
from requests.auth import HTTPProxyAuth
import re

async def normalize_url(url: str) -> str:
    """Функция форматирования URL"""
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        return url
    https_url = f"https://{url}"
    http_url = f"http://{url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(https_url, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status < 400:
                    return https_url
        except Exception:
            pass
        try:
            async with session.head(http_url, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status < 400:
                    return http_url
        except Exception:
            pass
    raise ValueError("Невозможно определить работающий URL")

async def is_valid_url(url: str) -> bool:
    """Функция валидации введенного сайта"""
    pattern = r'^[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, url))

async def check_url(url: str):
    """Функция проверки ресурса"""
    if not await is_valid_url(url):
        return f"{url} - некорректный формат URL"
    if not url.startswith(("http://", "https://")):
        url = await normalize_url(url)
    proxies = {
        "Латвия": ("http://185.122.206.243:4656", BasicAuth("user149714", "50lkae")),
        "Россия": (None, None),
        "Финляндия": ("http://109.196.106.122:2120", BasicAuth("user184781", "h7er2u")),
    }
    max_length = max(len(country) + (len(proxy[0]) if proxy[0] else 0) for country, proxy in proxies.items())
    results_list, results = [], {}

    async with aiohttp.ClientSession() as session:
        tasks = []

        for country, (proxy_url, proxy_auth) in proxies.items():
            if proxy_url and proxy_auth:
                task = asyncio.create_task(
                    session.get(url, proxy=proxy_url, proxy_auth=proxy_auth, timeout=aiohttp.ClientTimeout(total=5))
                )
            else:
                task = asyncio.create_task(session.get(url, timeout=aiohttp.ClientTimeout(total=5)))
            tasks.append((country, task))
            async with session.get("https://api.ipify.org", proxy=proxy_url,
                                   proxy_auth=proxy_auth if proxy_auth else None) as ip_response:
                ip = await ip_response.text()
            try:
                response = await task
                if response.status == 200:
                    results[f"{country} ({ip})"] = "✅ Ресурс доступен"
                elif response.status in range(400, 500):
                    results[
                        f"{country} ({ip})"] = f"⚠️ Ошибка при обращении к ресурсу: {response.status}"
                elif response.status in range(500, 600):
                    results[f"{country} ({ip})"] = "❌ Ресурс недоступен (ошибка сервера)"
                else:
                    results[f"{country} ({ip})"] = f"Неизвестный статус: {response.status}"
            except ClientSSLError as ssl_error:
                results[f"{country} ({ip})"] = f"❌ Ошибка SSL: {str(ssl_error)}"
            except ClientConnectionError as conn_error:
                results[f"{country} ({ip})"] = f"❌ Ошибка соединения: {str(conn_error)}"
            except TimeoutError:
                results[f"{country} ({ip})"] = "❌ Время ожидания соединения истекло"
            except ClientError as e:
                results[f"{country} ({ip})"] = f"❌ Прочая ошибка: {str(e)}"
            except Exception as e:
                results[f"{country} ({ip})"] = f"❌ Неизвестная ошибка: {str(e)}"
    for country, status in results.items():
        results_list.append(f"{country:<{max_length}}{status}")
    result_string = "\n".join(results_list)
    print(result_string)
    return result_string

async def main():
    """Функция проверки конкретного URL для отладки"""
    await check_url("https://test.com/")

if __name__ == "__main__":
    asyncio.run(main())
