import json
import requests
import asyncio
import aiohttp
import pandas as pd
from dotenv import load_dotenv

from config import API_TOKEN

load_dotenv()

api_token = API_TOKEN

# список ID IP-адресов через запятую
tm_list = 'ru1,jp1,au1,at1,am1,uk1,us1,tr1,se1,za1'

country_names = {
    'ru1': 'Россия',
    'jp1': 'Япония',
    'au1': 'Австралия',
    'at1': 'Австрия',
    'am1': 'Армения',
    'uk1': 'Великобритания',
    'us1': 'США',
    'tr1': 'Турция',
    'se1': 'Швеция',
    'za1': 'Южная Африка'
}

async def get_ip_ids():
    """Функция получения ID для всех IP-адресов сервиса ping-admin"""
    get_ip_ids_base_url = f'https://ping-admin.com/?a=api&sa=tm'
    get_ip_ids_url = f'{get_ip_ids_base_url}&api_key={api_token}'
    async with aiohttp.ClientSession() as session:
        async with session.get(get_ip_ids_url) as response:
            data = await response.text()
            df = pd.DataFrame(data)
            ids = df["id"].tolist()
            with open('ip_ids.txt', 'w') as file:
                for ip in ids:
                    file.write(ip + '\n')

async def add_task(testing_url: str) -> str:
    """Функция создания задачи"""
    add_task_base_url = f'https://ping-admin.com/?a=api&sa=new_task'

    # способ мониторинга (0 - случайные 30 IP-адресов, 1 - определенные IP-адреса из переменной 'tm')
    algoritm = 1

    # периодичность проверки (1 = раз в минуту, 2 = раз в 2 минуты и т.д.)
    period = 1

    # периодичность проверки во время ошибки
    period_error = 1

    # проверка на блокировку РКН
    rk = 1

    add_task_url = (f'{add_task_base_url}&api_key={api_token}&url={testing_url}&period={period}&period_error='
                    f'{period_error}&rk={rk}&algoritm={algoritm}&tm={tm_list}')
    async with aiohttp.ClientSession() as session:
        async with session.get(add_task_url) as response:
            text = await response.text()
            return text

async def get_info(task_id: int) -> str:
    """Функция получения статуса задачи"""
    get_info_base_url = f'https://ping-admin.com/?a=api&sa=task_stat&api_key={api_token}&id={task_id}'
    tasks_log_dict = {}
    async with aiohttp.ClientSession() as session:
        for tm in tm_list.split(','):
            get_info_url = f'{get_info_base_url}&tm={tm}'
            async with session.get(get_info_url) as response:
                tasks_log_dict[tm] = await response.text()
    return tasks_log_dict

async def delete_task(task_id: int):
    """Фугкция для удаления задачи"""
    delete_task_base_url = f'https://ping-admin.com/?a=api&sa=del_task'
    delete_task_url = f'{delete_task_base_url}&api_key={api_token}&id={task_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(delete_task_url) as response:
            try:
                if await response.text() == [{"status":"OK"}]:
                    return 'Успешно удалено'
            except Exception as e:
                return e

async def check_url(url: str) -> str:
    """Функция проверки ресурса"""
    add_task_result = json.loads(await add_task(url))
    if 'error' in add_task_result[0]:
        return f'Ошибка: {add_task_result[0]['error']}'
    else:
        task_id = add_task_result[0]['tid']
        status = await get_info(task_id)
        await asyncio.sleep(3)
        await delete_task(task_id)
        await process_result(status)
    return status

async def process_result(status: dict):
    """Функция обработки и вывода результата проверок по всем IP-адресам"""
    max_length = max(len(name) for name in country_names.values())
    total_width = max_length + 2  # Учитываем пробел и символ ✅/❌

    message_lines = []
    for country_code, json_str in status.items():
        data = json.loads(json_str)[0]
        uptime = data['uptime']
        status_icon = '✅' if uptime == 100 else '❌' if uptime == 0 else '⚠️'
        country_name = country_names.get(country_code, country_code)
        line = f"{country_name:<{max_length}}{status_icon}"
        message_lines.append(line)
    result = '\n'.join(message_lines)
    print(result)
    return result

test = {
    'ru1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]',
    'jp1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'au1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'at1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'am1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'uk1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'us1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'tr1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'se1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]', 
    'za1': '[{"tasks_logs":[],"uptime":100,"uptime_nw":0,"uptime_w":0}]'
    }

async def main():
    print(await process_result(test))

asyncio.run(main())