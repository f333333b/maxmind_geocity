from aiogram.types import BotCommand

commands = [
    BotCommand(command="/start", description="Запуск бота"),
    BotCommand(command="/check", description="Определение геолокации IP-адресов"),
    BotCommand(command="/target", description="Определение геолокации с фильтрацией по стране"),
    BotCommand(command="/filter", description="Отфильтровать IP-адреса"),
    BotCommand(command="/filter_octet", description="Отфильтровать IP-адреса по первому октету"),
    BotCommand(command="/help", description="Справка")
]