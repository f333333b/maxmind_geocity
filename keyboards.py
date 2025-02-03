from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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
    inline_keyboard=[[InlineKeyboardButton(text="Вывести строки с IP-адресами указанной страны", callback_data="copy_ips")]]
)