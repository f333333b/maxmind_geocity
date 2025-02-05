from aiogram.fsm.state import State, StatesGroup

# класс для состояния пользователя
class UserState(StatesGroup):
    START = State()
    HELP = State()
    BASIC_CHECK = State()
    TARGET_CHECK = State()
    FILTER_LIST = State()
    FILTER_OCTET = State()
    AWAITING_BASIC_CHECK = State()
    AWAITING_TARGET_CHECK = State()
    AWAITING_FILTER_LIST_FIRST = State()
    AWAITING_FILTER_LIST_SECOND = State()
    AWAITING_FILTER_OCTET_FIRST = State()
    AWAITING_FILTER_OCTET_SECOND = State()
    COPY_IPS = State()