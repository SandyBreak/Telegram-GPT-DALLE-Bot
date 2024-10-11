# -*- coding: UTF-8 -*-
import logging

from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram import Router, Bot, F

from services.postgres.user_service import UserService

from admin.admin_logs import send_log_message

from models.emojis import Emojis
from models.states import ChangeApiKeyStates

from exceptions.errors import UserNotRegError, AccessDeniedError

from config import CIPHER_SUITE

router = Router()


@router.message(Command(commands=['change_api_key']))
async def start(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    await state.clear()
    try:
        await UserService.check_user_rights(message.from_user.id)
        delete_message = await message.answer((f"Отправьте новый API ключ для вашего аккаунта:"))
        
        await state.set_state(ChangeApiKeyStates.get_and_change_api_key)
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Админстратор не дал вам доступ! {Emojis.ALLERT}\nПодождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    await state.update_data(message_id=delete_message.message_id)
    
    
@router.message(F.text, StateFilter(ChangeApiKeyStates.get_and_change_api_key))
async def get_and_change_api_key(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    message_log = False
    try:
        await UserService.save_data(message.from_user.id, 'encrypted_api_account_key', CIPHER_SUITE.encrypt((message.text).encode('utf-8')))
        message_log = await message.answer(f'{Emojis.SUCCESS} API ключ успешно изменён {Emojis.SUCCESS}')
        
    except Exception as e:
        logging.error(f'Ошбика смены API ключа у пользователя {message.from_user.id}: {e}')    
        message_log = await message.answer(f"{Emojis.FAIL} Ошибка смены ключа! {Emojis.FAIL}")
    if message_log: await send_log_message(message, bot, message_log)
    
    await state.clear()