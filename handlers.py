from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, CallbackQuery, ContentType
from messages import msg
from commands import commands
from states import UserState
from config import trusted_users
from keyboards import keyboard_main
from main_func import process_check, filter_ips_input, filter_ips_list, filter_by_octet, log_interaction, process_target_copy

router = Router()

@router.message(lambda message: message.content_type != ContentType.TEXT)
@log_interaction
async def unsupported_content_handler(message: Message):
    print('1')
    """Обработка ввода неподдерживаемых форматов данных - фото, документы и т.д."""
    return await message.answer(msg['invalid_input'])

@router.message(lambda message: message.text.startswith('/') and
                                not any(message.text == command.command for command in commands))
@log_interaction
async def unsupported_command_handler(message: Message):
    print('2')
    """Обработка ввода неверной команды"""
    return await message.answer(msg['invalid_command'])

@router.message(Command("start"))
@log_interaction
async def command_start_handler(message: Message, state: FSMContext):
    """Обработка команды /start"""
    current_state = await state.get_state()
    print(f"Текущее состояние пользователя: {current_state}")
    user_id = message.from_user.id
    if current_state is None:
        await state.set_state(UserState.START)
    if user_id in trusted_users:
        return await message.answer('Здравствуйте! Вы авторизованы. ' + msg['start'], reply_markup=keyboard_main)
    else:
        return await message.answer(msg['no_access'])

@router.message(Command("help"))
@log_interaction
async def command_help_handler(message: Message):
    """Обработка команды /help"""
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

@router.callback_query(StateFilter(UserState.COPY_IPS))
@log_interaction
async def copy_ips_callback_handler(query: CallbackQuery):
    """Обработка нажатия кнопки 'Вывести строки с IP-адресами указанной страны'"""
    user_id = query.from_user.id
    return await process_target_copy()

@router.message(UserState.AWAITING_FILTER_LIST_FIRST)
@log_interaction
async def process_filter_list_first_handler(message: Message, state: FSMContext):
    """Обработка первого списка в /filter"""
    user_id = message.from_user.id
    await state.set_state(UserState.AWAITING_FILTER_LIST_SECOND)
    return await message.answer(text=await filter_ips_input(message.text, user_id, list_flag=True, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_LIST_SECOND)
@log_interaction
async def process_filter_list_second_handler(message: Message, state: FSMContext):
    """Обработка второго списка в /filter"""
    user_id = message.from_user.id
    return await message.answer(text=await filter_ips_list(message.text, user_id, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_FIRST)
@log_interaction
async def process_filter_octet_first_handler(message: Message, state: FSMContext):
    """Обработка списка в /filter_octet"""
    await state.set_state(UserState.AWAITING_FILTER_OCTET_SECOND)
    user_id = message.from_user.id
    return await message.answer(text=await filter_ips_input(message.text, user_id, list_flag=False, state=state), parse_mode="HTML")

@router.message(UserState.AWAITING_FILTER_OCTET_SECOND)
@log_interaction
async def process_filter_octet_second_handler(message: Message, state: FSMContext):
    """Обработка октета в /filter_octet"""
    user_id = message.from_user.id
    return await message.answer(text=await filter_by_octet(message.text, user_id, state=state), parse_mode="HTML")

def register_handlers(dp):
    dp.include_router(router)