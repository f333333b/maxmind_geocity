from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# основная клавиатура
keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/check"),
        KeyboardButton(text="/target"),
        KeyboardButton(text="/filter_by_list"),
        KeyboardButton(text="/filter_by_octet")],
        [KeyboardButton(text="/remove_fourth_octet"),
        KeyboardButton(text="/remove_port"),
        KeyboardButton(text="/ping"),
        KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

keyboard_copy = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Вывести строки с IP-адресами указанной страны", callback_data="copy_ips")]]
)