from aiolimiter import AsyncLimiter
from aiogram.types import Update
from aiogram.dispatcher.middlewares.base import BaseMiddleware

# ограничение на количество допустимых сообщений в минуту
limiter = AsyncLimiter(30, 60)

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        if limiter.has_capacity():
            async with limiter:
                return await handler(event, data)
        else:
            if event.message:
                await event.message.answer("Превышено количество допустимых сообщений в минуту. Попробуйте позже.")
            return