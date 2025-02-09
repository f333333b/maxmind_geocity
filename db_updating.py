import asyncio
import logging
import os
import tarfile
import tempfile
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import aiofiles
import aiohttp

from config import database_filename, url

async def download_database():
    """Функция обновления базы данных"""
    async with aiohttp.ClientSession() as session:
        print('aiohttp.ClientSession() as session TEST_CALLED')
        try:
            async with session.get(url) as response:
                print('session.get(url) as response TEST_CALLED')
                if response.status == 200:
                    logging.info("Загрузка базы данных успешна (%s)", response.status)
                    async with aiofiles.open('database.tar.gz', 'wb') as file:
                        await file.write(await response.read())
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
                                async with aiofiles.open(target_file, 'rb') as src, aiofiles.open(destination_path, 'wb') as dest:
                                    await dest.write(await src.read())
                                archive.close()
                                try:
                                    os.remove('database.tar.gz')
                                except OSError as e:
                                    logging.warning("Не удалось удалить файл database.tar.gz: %s", e)
                                logging.info("Файл базы данных успешно обновлен.")
                            else:
                                logging.error("Файл %s не найден в архиве.", database_filename)
                else:
                    logging.error("Ошибка при скачивании базы данных. Статус:%s. Ошибка:%s.", response.status, await response.text())
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
                        last_modified = response.headers.get("Last-Modified")
                        if last_modified:
                            updated_base_date = parsedate_to_datetime(last_modified).replace(tzinfo=None)
                            if updated_base_date - existing_base_date > timedelta(weeks=1):
                                await download_database()
                except (aiohttp.ClientError, ValueError) as e:
                    logging.error(f"Ошибка при проверке обновлений базы: {e}")
        await asyncio.sleep(three_day_in_seconds)