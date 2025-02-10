from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# основная клавиатура
keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/check"),
        KeyboardButton(text="/target"),
        KeyboardButton(text="/filter"),
        KeyboardButton(text="/filter_octet"),
        KeyboardButton(text="/shorten"),
        KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Вывести строки с IP-адресами указанной страны", callback_data="copy_ips")]]
)

keyboard_choose_action = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Обрезать 4-ый октет", callback_data="remove_fourth_octet"),
         InlineKeyboardButton(text="Обрезать порт", callback_data="remove_the_port")],
    ]
)