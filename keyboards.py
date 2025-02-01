from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# кнопки для выбора действия
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

keyboard_choice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Определить геолокацию по IP-адресам", callback_data="basic_check")],
        [InlineKeyboardButton(text="Определить геолокацию с фильтрацией по стране", callback_data="target_check")],
        [InlineKeyboardButton(text="Отфильтровать IP-адреса", callback_data="filter_ips_1")],
        [InlineKeyboardButton(text="Отфильтровать IP-адреса по первому октету", callback_data="callback_filter_by_octet")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]

    ]
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отфильтровать IP-адреса по указанной стране", callback_data="copy_ips")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)

keyboard_back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)