import os
import aiohttp
import tarfile
import shutil
import tempfile
import logging
from config import database_filename, url, bot, user_states
from datetime import datetime, timedelta
from messages import msg

# функция для обновления базы
async def download_database(user_id):
    await bot.send_message(chat_id=user_id, text=msg['db_updating'])
    user_states[user_id] = 'awaiting_database_update'
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    with open('database.tar.gz', 'wb') as file:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        last_progress = -1
                        progress_message = await bot.send_message(chat_id=user_id, text=f'Выполняется скачивание базы данных: 0%')
                        async for chunk in response.content.iter_chunked(5000000):
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            progress = min(100, int(downloaded_size / total_size * 100))
                            if progress - last_progress >= 6:
                                last_progress = progress
                                await bot.edit_message_text(chat_id=user_id, message_id=progress_message.message_id,
                                    text=f"⏳ Выполняется скачивание базы данных: {progress}%")
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
                                await bot.edit_message_text(chat_id=user_id, message_id=progress_message.message_id, text=msg['db_updated'])
                                logging.info(f"Файл {database_filename} успешно обновлен.")
                            else:
                                logging.error(f"Файл {database_filename} не найден в архиве.")
                                await bot.send_message(chat_id=user_id, text=msg['db_update_error'])
                else:
                    await bot.send_message(chat_id=user_id, text=msg['db_update_error'])
                    logging.error(f"Ошибка при скачивании базы данных: {response.status}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке файла: {e}")
            await bot.send_message(chat_id=user_id, text=msg['db_update_error'])
    user_states[user_id] = 'back_to_choice'

# функция проверки наличия базы и ее актуальности
async def is_update_needed(user_id):
    if not os.path.exists(database_filename):
        await download_database(user_id)
    else:
        existing_base_date = datetime.fromtimestamp(os.path.getmtime(database_filename))
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as response:
                    if "Last-Modified" in response.headers:
                        updated_base_date = response.headers["Last-Modified"]
                        formatted_updated_base_date = datetime.strptime(updated_base_date, "%a, %d %b %Y %H:%M:%S %Z")
                        if formatted_updated_base_date - existing_base_date > timedelta(weeks=1):
                            await download_database(user_id)
            except:
                return 'error'