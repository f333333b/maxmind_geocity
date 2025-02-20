from aiogram.types import BotCommand

commands = [
    BotCommand(command="/start", description="Запуск бота"),
    BotCommand(command="/check", description="Определение геолокации IP-адресов"),
    BotCommand(command="/target", description="Определение геолокации с фильтрацией по стране"),
    BotCommand(command="/filter_by_list", description="Отфильтровать IP-адреса по списку"),
    BotCommand(command="/filter_by_octet", description="Отфильтровать IP-адреса по первому октету"),
    BotCommand(command="/remove_fourth_octet", description="Обрезать 4-ый октет"),
    BotCommand(command="/remove_port", description="Обрезать порт"),
    BotCommand(command="/help", description="Справка"),
    BotCommand(command="/ping", description="Ping IP")
]