# -*- coding: UTF-8 -*-

import logging
import numpy

from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram import Router, Bot, F


from config import LIST_USERS_TO_NEWSLETTER

from admin.admin_keyboards import AdminKeyboards
from admin.states import AdminPanelStates
from admin.assistant import AdminOperations

from services.postgres.admin_service import AdminService
from services.postgres.group_service import GroupService


from models.long_messages import ADMIN_MANUAL_MESSAGE
from models.emojis import Emojis


router = Router()


@router.message(Command('control'))
async def get_pass(message: Message, state: FSMContext) -> None:
    SUPER_GROUP_ID = await GroupService.get_group_id()
    if not(SUPER_GROUP_ID):
        logging.critical('Bot doesn''t activated')
    elif (message.chat.id == SUPER_GROUP_ID) and not(message.message_thread_id):
        root_keyboard = await AdminKeyboards.admin_possibilities_keyboard()     
        await message.answer(f'Выберите одно из нижеперечисленных действий', reply_markup=root_keyboard.as_markup())
        await state.set_state(AdminPanelStates.base_state)


@router.callback_query(F.data, StateFilter(AdminPanelStates.base_state))
async def choose_action(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    SUPER_GROUP_ID = await GroupService.get_group_id()
    if not(SUPER_GROUP_ID):
        logging.critical('Bot doesn''t activated')
        return
    
    action, user_id, user_tg_addr = await AdminOperations.parse_callback_data(callback.data)
    
    if action == 'manual_bot':
        await get_manual_admin_panel(callback)
        await callback.answer()
    if action == 'menu_bot':
        root_keyboard = await AdminKeyboards.admin_possibilities_keyboard()
        await callback.message.answer(f"Выберите одно из нижеперечисленных действий", reply_markup=root_keyboard.as_markup())
        await callback.answer()
    elif action == 'delete_menu':
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

        await callback.answer()
    elif action == 'newsletter':
        await callback.message.answer(f'Отправьте сообщение для рассылки:')
        await state.set_state(AdminPanelStates.launch_newsletter)
        await callback.answer()
    elif action == 'global':
        await newsletter(callback, state, bot, 'global')
        await callback.answer()
    elif action == 'targeted':
        list_users = await AdminKeyboards.keyboard_for_adding_users_in_targeted_newsletter()
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=list_users.as_markup())
        await callback.answer()
    elif action == 'cancel_newsletter':
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await state.set_state(AdminPanelStates.base_state)
        await callback.answer()
    elif action == 'accept_newsletter':
        await newsletter(callback, state, bot, 'targeted')
        await callback.answer()
    elif action == 'view_users':
        await view_user_stats(callback, bot)
    elif action == 'ADD':
        await add_user_to_newsletter(callback, user_id, user_tg_addr)
        update_list_users = await AdminKeyboards.keyboard_for_adding_users_in_targeted_newsletter(LIST_USERS_TO_NEWSLETTER)
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=update_list_users.as_markup())
    

async def get_manual_admin_panel(callback: CallbackQuery) -> None:
    await callback.message.answer(ADMIN_MANUAL_MESSAGE, ParseMode.HTML)
    await callback.answer()
    

@router.message(StateFilter(AdminPanelStates.launch_newsletter))
async def launch_newsletter(message: Message, state: FSMContext, bot: Bot) -> None:
    newsletter_keyboard = await  AdminKeyboards.newsletter_keyboard()
    edit_message = await bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=message.message_id, protect_content=None)
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=edit_message.message_id, reply_markup=newsletter_keyboard.as_markup())
    await state.set_state(AdminPanelStates.base_state)


async def add_user_to_newsletter(callback: CallbackQuery, user_id: str, user_tg_addr: str) -> None:
    if [user_list for user_list in LIST_USERS_TO_NEWSLETTER if user_id in user_list]:
        LIST_USERS_TO_NEWSLETTER.pop()
        await callback.answer()    
    else:
        LIST_USERS_TO_NEWSLETTER.append([user_id, user_tg_addr])
        await callback.answer()
        
        
async def newsletter(callback: CallbackQuery, state: FSMContext, bot: Bot, type_newsletter: str) -> None:
    if type_newsletter == 'global':
        user_data = await AdminService.get_table('user')
        user_ids_and_nicknames = [(user.id_tg, user.nickname) for user in user_data]
        user_data = numpy.array(user_ids_and_nicknames)
    if type_newsletter == 'targeted':
        user_data = numpy.array(LIST_USERS_TO_NEWSLETTER)
        
    if user_data.any():
        try:
            received_users = []
            not_received_users =[]
            for user in user_data:
                user_id = user[0]
                user_tg_addr = user[1]
                try:
                    await bot.copy_message(chat_id=user_id, from_chat_id=callback.message.chat.id, message_id=callback.message.message_id, protect_content=None)
                    received_users.append([user_id, user_tg_addr])
                except Exception as e:
                    if 'chat not found' in str(e):
                        logging.warning(f'Skipping user_id {user_id} due to ''chat not found'' error')
                        not_received_users.append([user_id, user_tg_addr, 'Чат не найден'])
                    elif 'bot was blocked' in str(e):
                        logging.warning(f'Skipping user_id {user_id} due to ''chat not found'' error')
                        not_received_users.append([user_id, user_tg_addr, 'Заблокировал бота'])
                    else:
                        logging.warning(f'Skipping user_id {user_id} unknown error{e}')
                        not_received_users.append([user_id, user_tg_addr, f'Другая ошибка{e}'])
            await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=None)
            message_report = 'Получившие пользователи:\n'
            if received_users:
                for user in received_users:
                    user_id=user[0]
                    user_tg_addr=user[1]
                    message_report += f'ID: {user_id} Адрес: {user_tg_addr}\n'

            if not_received_users:
                message_report += 'Не получившие пользователи:\n'
                for user in not_received_users:
                    user_id = user[0]
                    user_tg_addr = user[1]
                    reason = user[2]
                    message_report += f'ID: {user_id} Адрес: {user_tg_addr} Причина: {reason}\n' 
            LIST_USERS_TO_NEWSLETTER.clear()
            await callback.message.answer(f'{Emojis.SUCCESS} Рассылка завершена успешно!')
            await callback.message.answer(f'{message_report}')
            await state.set_state(AdminPanelStates.base_state)
        except Exception as e:
            logging.error(f'Error during newsletter: {e}')
    else:
        await callback.message.answer(f'{Emojis.ALLERT} Вы не добавили в рассылку ни одного пользователя')


async def view_user_stats(callback: CallbackQuery, bot: Bot) -> None:
    user_data = await AdminService.get_table('user')
    
    users_list_str = 'Список пользователей:\n\n'
    
    for user in user_data:
        users_list_str += f'ID: {user.id_tg}\nАдрес: {user.nickname}\n\n'
            
    await callback.message.answer(users_list_str)
    await callback.answer()