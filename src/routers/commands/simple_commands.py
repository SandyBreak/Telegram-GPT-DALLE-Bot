# -*- coding: UTF-8 -*-
import logging
import requests

from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Router, Bot
from models.user_keyboards import UserKeyboards
from models.emojis import Emojis
from admin.admin_logs import send_log_message
from services.postgres.user_service import UserService
from exceptions.errors import UserNotRegError, AccessDeniedError

router = Router()


@router.message(Command(commands=['balance']))
async def check_balance(message: Message, state: FSMContext, bot: Bot) -> None:
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




@router.message(Command(commands=['mode']))
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    await state.clear()
    try:
        await UserService.check_user_rights(message.from_user.id)
        ai_models_keyboard = await UserKeyboards.ai_models_keyboard(message.from_user.id)
        delete_message = await message.reply("выберите модель", reply_markup=ai_models_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
        
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer("Админстратор не дал вам доступ. Подождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    await state.update_data(message_id=delete_message.message_id)
        
    
    

@router.message(Command(commands=['role']))
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    pass


