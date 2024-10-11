# -*- coding: UTF-8 -*-

from aiogram.fsm.state import State, StatesGroup


class RegUserStates(StatesGroup):
    """
    Состояния регистрации пользователя
    """
    get_fio = State()
    get_phone_number = State()
    get_api_key = State()


class ChangeApiKeyStates(StatesGroup):
    """
    Состояния смены API ключа
    """
    get_and_change_api_key = State()


class CreateRoleStates(StatesGroup):
    """
    Состояния создания новой роли
    """
    get_name = State()
    get_system_promt_and_create_role = State()


class ChangeSystemPromt(StatesGroup):
    """
    Состояния изменения контекста роли
    """
    get_and_change_system_promt = State()
