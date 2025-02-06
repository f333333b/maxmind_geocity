import os
import logging
from functools import wraps
from config import user_loggers
from aiogram.types import Message, CallbackQuery, ContentType


async def setup_user_logger(user_id):
    """Функция запуска логирования"""
    if user_id in user_loggers:
        user_loggers[user_id]
    log_filename = "logs/{}.log".format(user_id)
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logger = logging.getLogger(str(user_id))
    # отключение вывода логирования в консоль
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(log_filename, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    user_loggers[user_id] = logger
    return logger

def log_interaction(func):
    """Функция-декоратор для логирования сообщений"""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        logger = await setup_user_logger(user_id)
        if isinstance(event, Message):
            if event.content_type == ContentType.TEXT:
                text = event.text
                logger.info("Пользователь (%s) отправил сообщение:\n%s", user_id, text)
            else:
                logger.info("Пользователь (%s) отправил неподдерживаемый формат контента:\n%s", user_id, event.content_type)
        elif isinstance(event, CallbackQuery):
            data = event.data
            logger.info("Пользователь (%s) нажал кнопку:\n%s", user_id, data)
        bot_response = await func(event, *args, **kwargs)
        if bot_response:
            if isinstance(bot_response, Message):
                logger.info("Ответ бота:\n%s", bot_response.text if bot_response.text else "Текст отсутствует")
            elif isinstance(bot_response, CallbackQuery):
                logger.info("Ответ бота:\n%s", bot_response.data)
            else:
                logger.info("Ответ бота:\n%s", str(bot_response))
        else:
            logger.info("Ответ бота:\nпусто")
        return bot_response
    return wrapper