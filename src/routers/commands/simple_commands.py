# -*- coding: UTF-8 -*-
import logging
import requests

from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram import Router, Bot

from admin.admin_logs import send_log_message

from models.emojis import Emojis

from services.postgres.user_service import UserService
from services.postgres.role_management_service import RoleManagmentService

from exceptions.errors import UserNotRegError, AccessDeniedError

router = Router()


@router.message(Command(commands=['balance']))
async def check_balance(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Вывод баланса пользователя
    """
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    
    await state.clear()
    message_log = False
    delete_message = False
    
    try:
        await UserService.check_user_rights(message.from_user.id)
        
        openai_api_key = await UserService.get_user_data(message.from_user.id, 'encrypted_api_account_key')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        response = requests.post("https://api.proxyapi.ru/proxyapi/balance", headers=headers)

        if response.status_code == 200:
            message_log = await message.answer(f"Баланс: {response.json()['balance']} рублей")
        else:
            logging.error("Error:", response.status_code, response.text)
            message_log = await message.answer(f'{Emojis.FAIL} Ошибка проверки баланса!{Emojis.FAIL}\nStatus code: {response.status_code}\nResponse text: {response.text}')
    
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer("Админстратор не дал вам доступ. Подождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    
    if delete_message: await state.update_data(message_id=delete_message.message_id)
    if message_log: await send_log_message(message, bot, message_log)
    
    
    
    
@router.message(Command(commands=['view_set_options']))
async def view_set_options(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Вывод текущих настроек пользователя
    """
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    
    await state.clear()
    message_log = False
    delete_message = False
    try:
        await UserService.check_user_rights(message.from_user.id)
        temporary_user_data = await RoleManagmentService.get_temporary_user_data(message.from_user.id, 'all')
        
        setup_message = f"""
<b>Выбранная языковая модель:</b> {temporary_user_data.llm_model}
        
<b>Роль:</b> {temporary_user_data.name_role}

<b>Контекст роли:</b> {temporary_user_data.history_dialog[0]['content']}
        
<b>Выбранная генеративная модель:</b> {temporary_user_data.img_model}
        
<b>Качество генерируемого изображения:</b> {temporary_user_data.quality_generated_image}
"""
        
        delete_message = await message.answer(setup_message, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
    
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer("Админстратор не дал вам доступ. Подождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    
    if delete_message: await state.update_data(message_id=delete_message.message_id)
    if message_log: await send_log_message(message, bot, message_log)