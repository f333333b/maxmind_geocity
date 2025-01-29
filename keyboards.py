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
        [InlineKeyboardButton(text="Проверить страну по IP-адресу", callback_data="check_country")],
        [InlineKeyboardButton(text="Фильтровать IP", callback_data="filter_ips_1")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")]

    ]
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отфильтровать IP-адреса по стране", callback_data="copy_ips")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)

keyboard_back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)