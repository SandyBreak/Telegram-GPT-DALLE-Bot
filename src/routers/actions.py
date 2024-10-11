# -*- coding: UTF-8 -*-

import logging
import json

from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.types import Message, CallbackQuery
from aiogram import Router, Bot, F

from models.emojis import Emojis

from services.postgres.group_service import GroupService
from services.postgres.user_service import UserService

router = Router()

    
@router.my_chat_member()
async def my_chat_member_handler(message: Message, bot: Bot) -> None:
    """
    Обработка события когда бот добавлен в группу и сохранение ID группы в базе данных
    """
    if message.new_chat_member.status == ChatMemberStatus.MEMBER:
        member = message.new_chat_member
        if member.user.id == bot.id and message.from_user.id == 5890864355:  # Проверяем, добавлен ли бот
            await message.answer('Спасибо за добавление меня в группу! Для моей правильной работы назначьте меня администратором!')
            
            if message.chat.id != message.from_user.id:
                await GroupService.group_init(message.chat.id)
            
            logging.warning(f'Bot was added in group! ID: {message.chat.id}, adder_ID: {message.from_user.id}, adder_addr: {message.from_user.username}')
        
        elif message.from_user.id != 5890864355:
            await bot.send_message(5890864355, text=f'{Emojis.ALLERT} Бот был добавлен в группу без разрешения!\nCHAT_ID: {message.chat.id}\nID: {message.from_user.id}\nАдрес: @{message.from_user.username}')
            await message.answer('У вас нету прав чтобы добавлять меня в эту группу, до свидания!')
            await bot.leave_chat(message.chat.id)
    if message.new_chat_member.status == ChatMemberStatus.LEFT:
        if message.from_user.id == bot.id:
            logging.critical(f'Bot was illegally added to the group!')
        else:
            logging.critical(f'Bot was kikked from group! ID: {message.chat.id}, adder_ID: {message.from_user.id}, adder_addr: {message.from_user.username}')
            await GroupService.group_reset()
    elif message.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
        await message.answer('Теперь я администратор!')


@router.callback_query(lambda F: 'allow_access' in F.data or 'deny_access' in F.data or 'temporarily_restrict_access' in F.data)
async def access_request_processing(callback: CallbackQuery, bot: Bot) -> None:
    data = json.loads(callback.data)
    if data['key'] == 'allow_access':
        await UserService.save_data(data['value'], 'access_flag', True)
        await bot.send_message(chat_id=data['value'], text=f'{Emojis.SUCCESS} Доступ разрешен! {Emojis.SUCCESS}\n\n Введите команду /help для того чтобы ознакомиться с функциями бота.')
    elif data['key'] == 'temporarily_restrict_access':
        await UserService.save_data(data['value'], 'access_flag', False)
        await bot.send_message(chat_id=data['value'], text=f'{Emojis.ALLERT} Доступ временно ограничен! {Emojis.ALLERT}')
    elif data['key'] == 'deny_access':
        await UserService.delete_user(data['value'])
        await bot.send_message(chat_id=data['value'], text=f'{Emojis.FAIL} Доступ запрещен! {Emojis.FAIL}\n\n Ваш аккаунт удален администратором.')
    await callback.answer()
    

@router.callback_query(F.data == "{\"key\": null}")
async def nothing_allert(callback: CallbackQuery) -> None:
    data = json.loads(callback.data)
    if not(data['key']):
        await callback.answer(text='Эта кнопка ничего не делает', show_alert=True)