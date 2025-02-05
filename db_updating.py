import os
import aiohttp
import tarfile
import shutil
import tempfile
import logging
import asyncio
from config import database_filename, url
from datetime import datetime, timedelta

async def download_database():
    """Функция обновления базы данных"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    with open('database.tar.gz', 'wb') as file:
                            file.write(await response.read())
                    with tarfile.open('database.tar.gz', 'r:gz') as archive:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            target_file = None
                            for filename in archive.getnames():
                                if os.path.basename(filename) == database_filename:
                                    archive.extract(filename, path=temp_dir)
                                    target_file = os.path.join(temp_dir, filename)
                                    break
                            if target_file and os.path.exists(target_file):
                                program_directory = os.path.dirname(os.path.abspath(__file__))
                                destination_path = os.path.join(program_directory, database_filename)
                                shutil.copy2(target_file, destination_path)
                                archive.close()
                                os.remove('database.tar.gz')
                                logging.info("Файл базы данных успешно обновлен.")
                            else:
                                logging.error("Файл %s не найден в архиве.", database_filename)
                else:
                    logging.error("Ошибка при скачивании базы данных: %s", response.status)
        except Exception as e:
            logging.error("Ошибка при загрузке файла: %s", e)

async def update_check():
    """Функция проверки наличия базы и ее актуальности"""
    three_day_in_seconds = 3 * 24 * 60 * 60
    while True:
        if not os.path.exists(database_filename):
            await download_database()
        else:
            existing_base_date = datetime.fromtimestamp(os.path.getmtime(database_filename))
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url) as response:
                        if "Last-Modified" in response.headers:
                            updated_base_date = response.headers["Last-Modified"]
                            formatted_updated_base_date = datetime.strptime(updated_base_date, "%a, %d %b %Y %H:%M:%S %Z")
                            if formatted_updated_base_date - existing_base_date > timedelta(weeks=1):
                                await download_database()
                except:
                    return 'error'
        await asyncio.sleep(three_day_in_seconds)