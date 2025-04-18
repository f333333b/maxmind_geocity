import os
import asyncio
import logging
from functools import wraps
from aiogram.types import Message, CallbackQuery, ContentType
from config import user_loggers
from config import ADMIN_ID, NOTIFY_ADMIN

async def setup_user_logger(user_id):
    """Функция запуска логирования"""
    if user_id in user_loggers:
        return user_loggers[user_id]
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

async def logs_to_db():
    one_day_in_seconds = 24 * 60 * 60
    while True:
        log_path = r'test_logs'
        for filename in filter(lambda x: x.endswith('.log'), os.listdir(log_path)):
            with open(log_path + '/' + filename, 'r') as file:
                print('test')
        await asyncio.sleep(one_day_in_seconds)

def notify_admin(handler):
    '''Функция-декоратор для отправки информации о работе бота администратору'''
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        result = await handler(event, *args, **kwargs)
        if not NOTIFY_ADMIN:
            return result
        user_id = getattr(getattr(event, "from_user", None), "id", "unknown")
        payload = getattr(event, "text", None) or getattr(event, "data", None) or "<unknown input>"
        reply = (
                getattr(result, "text", None)
                or (result[0].text if isinstance(result, list) and hasattr(result[0], "text") else None)
                or "<non-textual reply>"
        )
        try:
            await event.bot.send_message(
                ADMIN_ID,
                f"🔔 <b>User</b>: <code>{user_id}</code>\n"
                f"📨 <b>Input</b>: <code>{payload}</code>\n"
                f"🤖 <b>Reply</b>: <code>{reply}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return result
    return wrapper
