from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ContentType, Message

from commands import commands
from config import TRUSTED_USERS
from filter_utils import filter_by_octet, filter_ips_input, filter_ips_list, shorten_ips
from geoip_utils import process_check, process_target_copy
from keyboards import keyboard_main, keyboard_choose_action
from logging_utils import log_interaction
from messages import msg
from states import UserState

router = Router()

@router.message(StateFilter(None))
@log_interaction
async def default_state_handler(message: Message, state: FSMContext):
    """Обработка стандартного состояния"""
    user_id = message.from_user.id
    if user_id in TRUSTED_USERS:
        await state.set_state(UserState.START)
        return await message.answer('Здравствуйте! Вы авторизованы. ' + msg['start'], reply_markup=keyboard_main)
    else:
        return await message.answer(msg['no_access'])

@router.message(lambda message: message.content_type != ContentType.TEXT)
@log_interaction
async def unsupported_content_handler(message: Message):
    """Обработка ввода неподдерживаемых форматов данных - фото, документы и т.д."""
    return await message.answer(msg['invalid_input'])

@router.message(lambda message: message.text.startswith('/') and
                                not any(message.text == command.command for command in commands))
@log_interaction
async def unsupported_command_handler(message: Message):
    """Обработка ввода неверной команды"""
    return await message.answer(msg['invalid_command'])

@router.message(Command("start"))
@log_interaction
async def command_start_handler(message: Message):
    """Обработка команды /start"""
    return await message.answer(msg['start'], reply_markup=keyboard_main)

@router.message(Command("help"))
@log_interaction
async def command_help_handler(message: Message, state: FSMContext):
    """Обработка команды /help"""
    await state.set_state(UserState.START)
    return await message.answer(msg['help'], parse_mode='HTML', disable_web_page_preview=True)

@router.message(Command("check"))
@log_interaction
async def command_check_handler(message: Message, state: FSMContext):
    """Обработка команды /check"""
    await state.set_state(UserState.AWAITING_BASIC_CHECK)
    return await message.answer(msg["enter_check_ips"])

@router.message(Command("target"))
@log_interaction
async def command_target_handler(message: Message, state: FSMContext):
    """Обработка команды /target"""
    await state.set_state(UserState.AWAITING_TARGET_CHECK)
    return await message.answer(msg['enter_target_ips'])

@router.message(Command("filter"))
@log_interaction
async def command_filter_list_handler(message: Message, state: FSMContext):
    """Обработка команды /filter"""
    await state.set_state(UserState.AWAITING_FILTER_LIST_FIRST)
    return await message.answer(msg['filter_ips_first'])

@router.message(Command("filter_octet"))
@log_interaction
async def command_filter_octet_handler(message: Message, state: FSMContext):
    """Обработка команды /filter_octet"""
    await state.set_state(UserState.AWAITING_FILTER_OCTET_FIRST)
    return await message.answer(msg['filter_ips_first'])

@router.message(Command("shorten"))
@log_interaction
async def command_shorten_handler(message: Message, state: FSMContext):
    """Обработка команды /shorten"""
    await state.set_state(UserState.AWAITING_FILTER_SHORTEN_LIST)
    return await message.answer(msg['filter_ips_first'])

@router.message(UserState.START)
@log_interaction
async def state_start_handler(message: Message):
    """Обработка состояния START"""
    return await message.answer(msg['start'], reply_markup=keyboard_main)

@router.message(UserState.AWAITING_BASIC_CHECK)
@log_interaction
async def process_check_handler(message: Message):
    """Обработка функции /check - ввода текста"""
    user_id = message.from_user.id
    return await process_check(message, user_id, target_flag=False)

@router.message(UserState.AWAITING_TARGET_CHECK)
@log_interaction
async def process_target_handler(message: Message):
    """Обработка функции /target - ввода текста"""
    user_id = message.from_user.id
    return await process_check(message, user_id, target_flag=True)

@router.message(UserState.AWAITING_FILTER_LIST_FIRST)
@log_interaction
async def process_filter_list_first_handler(message: Message, state: FSMContext):
    """Обработка ввода первого списка в /filter"""
    await state.set_state(UserState.AWAITING_FILTER_LIST_SECOND)
    return await message.answer(text=await filter_ips_input(message.text, filter_type='filter_by_list', state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_SHORTEN_LIST)
@log_interaction
async def shorten_list_input_handler(message: Message, state: FSMContext):
    """Обработка ввода списка в /shorten"""
    return await message.answer(text=await filter_ips_input(message.text, filter_type='shorten', state=state),
                                parse_mode="HTML", reply_markup=keyboard_choose_action)

@router.message(UserState.AWAITING_FILTER_LIST_SECOND)
@log_interaction
async def process_filter_list_second_handler(message: Message, state: FSMContext):
    """Обработка ввода второго списка в /filter"""
    return await message.answer(text=await filter_ips_list(message.text, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_FIRST)
@log_interaction
async def process_filter_octet_first_handler(message: Message, state: FSMContext):
    """Обработка ввода списка в /filter_octet"""
    await state.set_state(UserState.AWAITING_FILTER_OCTET_SECOND)
    return await message.answer(text=await filter_ips_input(message.text, filter_type='filter_by_octet', state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_SECOND)
@log_interaction
async def process_filter_octet_second_handler(message: Message, state: FSMContext):
    """Обработка ввода октета в /filter_octet"""
    return await message.answer(text=await filter_by_octet(message.text, state=state), parse_mode="HTML")


# callback-обработчики
@router.callback_query(F.data == "copy_ips")
@log_interaction
async def copy_ips_callback_handler(query: CallbackQuery):
    """Обработка нажатия кнопки 'Вывести строки с IP-адресами указанной страны'"""
    user_id = query.from_user.id
    return await query.message.answer(text=await process_target_copy(user_id), parse_mode="HTML")

@router.callback_query(F.data == "remove_fourth_octet")
@log_interaction
async def remove_fourth_octet_callback_handler(query: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Обрезать 4-ый октет'"""
    return (await query.message.answer(text=await shorten_ips(octet_flag=True, state=state), parse_mode="HTML"),
            await query.message.answer(msg["process_ips"]))

@router.callback_query(F.data == "remove_the_port")
@log_interaction
async def remove_the_port_callback_handler(query: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Обрезать порт'"""
    return (await query.message.answer(text=await shorten_ips(octet_flag=False, state=state), parse_mode="HTML"),
            await query.message.answer(msg["process_ips"]))

def register_handlers(dp):
    dp.include_router(router)