from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# кнопки для выбора действия
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# постоянная клавиатура
keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/check"),
        KeyboardButton(text="/target"),
        KeyboardButton(text="/filter"),
        KeyboardButton(text="/filter_octet"),
        KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отфильтровать IP-адреса по указанной стране", callback_data="copy_ips")]
    ]
)

keyboard_back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_choice")]
    ]
)