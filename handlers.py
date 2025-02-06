from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import ContentType, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from messages import msg
from commands import commands
from states import UserState
from config import trusted_users
from logging_utils import log_interaction
from keyboards import keyboard_main
from geoip_utils import process_check, process_target_copy
from filter_utils import filter_ips_input, filter_ips_list, filter_by_octet

router = Router()

@router.message(StateFilter(None))
@log_interaction
async def default_state_handler(message: Message, state: FSMContext):
    """Обработка стандартного состояния"""
    user_id = message.from_user.id
    if user_id in trusted_users:
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
async def command_start_handler(message: Message, state: FSMContext):
    """Обработка команды /start"""
    return await message.answer(msg['start'], reply_markup=keyboard_main)

@router.message(Command("help"))
@log_interaction
async def command_help_handler(message: Message, state: FSMContext):
    """Обработка команды /help"""
    await state.set_state(UserState.START)
    return await message.answer(msg['help'], parse_mode='HTML')

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

@router.callback_query(F.data == "copy_ips")
@log_interaction
async def copy_ips_callback_handler(query: CallbackQuery):
    """Обработка нажатия кнопки 'Вывести строки с IP-адресами указанной страны'"""
    user_id = query.from_user.id
    return await query.message.answer(text=await process_target_copy(user_id), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_LIST_FIRST)
@log_interaction
async def process_filter_list_first_handler(message: Message, state: FSMContext):
    """Обработка ввода первого списка в /filter"""
    user_id = message.from_user.id
    await state.set_state(UserState.AWAITING_FILTER_LIST_SECOND)
    return await message.answer(text=await filter_ips_input(message.text, user_id, list_flag=True, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_LIST_SECOND)
@log_interaction
async def process_filter_list_second_handler(message: Message, state: FSMContext):
    """Обработка ввода второго списка в /filter"""
    user_id = message.from_user.id
    return await message.answer(text=await filter_ips_list(message.text, user_id, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_FIRST)
@log_interaction
async def process_filter_octet_first_handler(message: Message, state: FSMContext):
    """Обработка ввода списка в /filter_octet"""
    await state.set_state(UserState.AWAITING_FILTER_OCTET_SECOND)
    user_id = message.from_user.id
    return await message.answer(text=await filter_ips_input(message.text, user_id, list_flag=False, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_SECOND)
@log_interaction
async def process_filter_octet_second_handler(message: Message, state: FSMContext):
    """Обработка ввода октета в /filter_octet"""
    user_id = message.from_user.id
    return await message.answer(text=await filter_by_octet(message.text, user_id, state=state), parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)