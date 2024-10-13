# -*- coding: UTF-8 -*-

from typing import Optional

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from services.postgres.admin_service import AdminService

from models.emojis import Emojis


class AdminKeyboards:
    def __init__(self) -> None:
        pass

    
    @staticmethod
    async def newsletter_keyboard() -> InlineKeyboardBuilder:
        '''
        Клавиатура для рассылки
        '''
        builder = InlineKeyboardBuilder(
            markup=[
                [
                    InlineKeyboardButton(text='Запустить глобальную рассылку', callback_data=f'global')
                ],
                [
                    InlineKeyboardButton(text='Запустить точечную рассылку', callback_data=f'targeted')
                ],
                [
                    InlineKeyboardButton(text='Удалить это сообщение', callback_data=f'cancel_newsletter')
                ]
            ]
        )
        return builder
    
    
    @staticmethod
    async def keyboard_for_adding_users_in_targeted_newsletter(added_users: Optional[list] = None) -> InlineKeyboardBuilder:
        '''
        Клавиатура с выбором пользователей для точечной рассылки
        '''
        builder = InlineKeyboardBuilder()
        users = await AdminService.get_table('user')
        if added_users:
            for user in users:
                user_id = user.id_tg
                user_tg_addr = user.nickname
                for added_user in added_users:
                    added_user_id = int(added_user[0])
                    added_user_tg_addr = added_user[1]
                    if user_id == added_user_id and user_tg_addr == added_user_tg_addr:        
                        builder.row(InlineKeyboardButton(text=f'{Emojis.SUCCESS} {added_user_id} {added_user_tg_addr}', callback_data=f'ADD,{added_user_id},{added_user_tg_addr}'))
                        break
                else:
                    builder.row(InlineKeyboardButton(text=f'{Emojis.FAIL} {user_id} {user_tg_addr}', callback_data=f'ADD,{user_id},{user_tg_addr}'))
            
        else:        
            for user in users:
                user_id = user.id_tg
                user_tg_addr = user.nickname
                builder.row(InlineKeyboardButton(text=f'{Emojis.FAIL} {user_id} {user_tg_addr}', callback_data=f'ADD,{user_id},{user_tg_addr}'))

        builder.row(InlineKeyboardButton(text=f'Отправить выбраным пользователям', callback_data=f'accept_newsletter'))
        
        return builder
    
    
    @staticmethod
    async def admin_possibilities_keyboard() -> InlineKeyboardBuilder:
        """
        Основная клавиатура админа
        """
        builder = InlineKeyboardBuilder(
            markup=[
                [
                    InlineKeyboardButton(text="РУКОВОДСТВО АДМИН ПАНЕЛИ", callback_data=f'manual_bot')
                ],
                [
                    InlineKeyboardButton(text="Запустить рассылку", callback_data=f'newsletter')
                ],
                [
                    InlineKeyboardButton(text="Посмотреть список пользователей", callback_data=f'view_users')
                ],
                [
                    InlineKeyboardButton(text="Заново отправить сообщение с действиями", callback_data='menu_bot')
                ],
                [
                    InlineKeyboardButton(text="Отмена", callback_data='delete_menu')
                ]
            ]
        )
        return builder