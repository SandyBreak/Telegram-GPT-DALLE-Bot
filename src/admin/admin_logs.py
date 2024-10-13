# -*- coding: UTF-8 -*-

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram import Bot
import logging

from services.postgres.group_service import GroupService
from services.postgres.user_service import UserService

from models.emojis import Emojis


async def send_log_message(message: Message, bot: Bot, message_log) -> None:
    """Отправка сообщения в админ группу

    Args:
        message (Message): This object represents a message.
        bot (Bot): Bot class
        message_log (_type_): Сообщение которое отправляем
    """
    SUPER_GROUP_ID = await GroupService.get_group_id()
    
    if not(SUPER_GROUP_ID):
        logging.critical('Bot doesn''t activated')
        return
    
    id_topic_chat = await GroupService.get_user_message_thread_id(message.from_user.id)
    '''
    Если у пользователя нету id темы с его именем
    '''
    if not(id_topic_chat):
        try:
            '''
            Создаем новую тему
            '''
            new_topic = await bot.create_forum_topic(chat_id=SUPER_GROUP_ID, name=message.from_user.full_name)
            await GroupService.save_user_message_thread_id(message.from_user.id, new_topic.message_thread_id)
        except TelegramBadRequest as e:
            if 'not enough rights' in str(e):
                    logging.error(f'Not enough rights!')
                    await bot.send_message(chat_id=SUPER_GROUP_ID, text=f'{Emojis.ALLERT} Обнаружен новый пользователь! {Emojis.ALLERT}\n\nЯ не могу создать новый диалог с ним из-за того у моих прав недостаточно!\n\nНазначьте меня администратором!')
                    return
        except Exception as e:
            logging.error(f'Error create forum topic: {e}')
        '''
        Отправляем сообщение с информацией о пользователе и закрепляем его
        '''
        user_data = await UserService.get_user_data(message.from_user.id, 'all')
        new_user_message = await bot.send_message(chat_id=SUPER_GROUP_ID, text=f'ID пользователя: {user_data.id_tg}\nТелеграмм имя пользователя: {user_data.fullname}\nФИО: {user_data.fio}\nАдрес пользователя: @{user_data.nickname}\nID темы: {new_topic.message_thread_id}', reply_to_message_id=new_topic.message_thread_id)
        
        await bot.pin_chat_message(chat_id=SUPER_GROUP_ID, message_id=new_user_message.message_id)
        await bot.copy_message(chat_id=SUPER_GROUP_ID, from_chat_id=message_log.chat.id, message_id=message_log.message_id, message_thread_id=new_topic.message_thread_id, protect_content=None)
    elif id_topic_chat:
        try:
            await bot.copy_message(chat_id=SUPER_GROUP_ID, from_chat_id=message_log.chat.id, message_id=message_log.message_id, message_thread_id=id_topic_chat, protect_content=None)
        except TelegramBadRequest as e:
                '''
                Если тема была удалена
                '''
                if 'message thread not found' in str(e):
                    logging.error(f'Message thread not found')
                    try:
                        '''
                        Создаем новую тему
                        '''
                        new_topic = await bot.create_forum_topic(chat_id=SUPER_GROUP_ID, name=message.from_user.full_name)
                        await GroupService.save_user_message_thread_id(message.from_user.id, new_topic.message_thread_id)
                    except TelegramBadRequest as e:
                        if 'not enough rights' in str(e):
                                logging.error(f'Not enough rights!')
                                await bot.send_message(chat_id=SUPER_GROUP_ID, text='Назначьте меня администратором!')
                                return
                    except Exception as e:
                        logging.error(f'Error create forum topic: {e}')
                        
                    '''
                    Отправляем сообщение с информацией о пользователе и закрепляем его
                    '''
                    user_data = await UserService.get_user_data(message.from_user.id, 'all')
                    new_user_message = await bot.send_message(chat_id=SUPER_GROUP_ID, text=f'ID пользователя: {user_data.id_tg}\nТелеграмм имя пользователя: {user_data.fullname}\nФИО: {user_data.fio}\nАдрес пользователя: @{user_data.nickname}\nID темы: {new_topic.message_thread_id}', reply_to_message_id=new_topic.message_thread_id)
        
                    await bot.pin_chat_message(chat_id=SUPER_GROUP_ID, message_id=new_user_message.message_id)
                    await bot.copy_message(chat_id=SUPER_GROUP_ID, from_chat_id=message_log.chat.id, message_id=message_log.message_id, message_thread_id=new_topic.message_thread_id, protect_content=None)
                else:
                    logging.error(f'Unknown error: {e}')