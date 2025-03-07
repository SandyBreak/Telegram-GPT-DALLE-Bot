# -*- coding: UTF-8 -*-
import logging
import base64

from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram import Router, Bot

from openai import AsyncOpenAI, APIStatusError

from admin.admin_logs import send_log_message

from models.emojis import Emojis

from services.postgres.role_management_service import RoleManagmentService
from services.postgres.user_service import UserService

from exceptions.errors import UserNotRegError, AccessDeniedError

from utils.assistant import MinorOperations

router = Router()


@router.message(Command(commands=['img']))
async def generate_igm(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Генерация изображения при помощи генеративной модели
    """
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    await state.clear()
    
    message_log = False #сообщение для логов в чат с пользователем в группе
    delete_message = False #сообщение для удаления
    load_message = False
    generated_image_quality='standard'
    
    try:
        await UserService.check_user_rights(message.from_user.id)
        primary_balance = await MinorOperations.check_balance(message.from_user.id)

        openai_api_key = await UserService.get_user_data(message.from_user.id, 'encrypted_api_account_key')
        
        temporary_user_data = await RoleManagmentService.get_temporary_user_data(message.from_user.id, 'all')
        
        if temporary_user_data.img_model == 'dall-e-3-hd':
            generated_image_quality='hd'
            
        query_text = message.text[len('/img '):].strip()
        
        if query_text:
            load_message = await message.answer(f'{Emojis.TIME} Генерация изображения...')
            try:
                client = AsyncOpenAI(api_key=openai_api_key, base_url="https://api.proxyapi.ru/openai/v1")
                
                response = await client.images.generate(
                    prompt=query_text,
                    model=temporary_user_data.img_model if temporary_user_data.img_model != 'dall-e-3-hd' else 'dall-e-3',
                    n=1,  # Количество изображений для генерации
                    quality=generated_image_quality,
                    response_format="url",
                    size=temporary_user_data.quality_generated_image,  # Размер изображения
                    style="vivid"
                )
                #photo_file_path = f'downloads/generated_image{message.from_user.id}.png'
                #print(response)
                #with open(photo_file_path, 'wb') as photo_file:
                #    photo_file.write(base64.b64decode(response.data[0].b64_json))
                
                #photo = FSInputFile(photo_file_path)
                
                secondary_balance = await MinorOperations.check_balance(message.from_user.id)
                #message_log = await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=f"<b>Вы запросили изображение по запросу</b>:\n{query_text}\n\n Стоимость: {primary_balance-secondary_balance} рублей", parse_mode=ParseMode.HTML)
                message_log = await message.answer(f"<b>Вы запросили <a href='{response.data[0].url}'>ИЗОБРАЖЕНИЕ</a> по запросу</b>:\n{query_text}\n\n Стоимость: {primary_balance-secondary_balance} рублей", parse_mode=ParseMode.HTML)
            except APIStatusError as e:
                error_detail = e.response.json()
                if "Insufficient balance" in error_detail.get('detail'):
                    message_log = await message.answer(f"{Emojis.FAIL} Недостаточно средств для совершения операции! {Emojis.FAIL}\n\n Текущий баланс: {primary_balance} рублей")
                    logging.error(f"Маленький баланс у пользователя {message.from_user.id}: {e}")
                elif "Invalid API Key" in error_detail.get('detail'):
                    message_log = await message.answer(f"{Emojis.FAIL} Неверный API ключ! {Emojis.FAIL}\n\nЧтобы поменять введите /change_api_key")
                    logging.error(f"Неверный API ключ у пользователя {message.from_user.id}: {e}")
                else:
                    message_log = await message.answer("Извините, произошла ошибка. Сообщение администратору уже отправлено")
                    logging.error(f"Ошибка при генерации изображения у пользователя {message.from_user.id}: {e}")
            except Exception as e:
                message_log = await message.answer("Извините, произошла ошибка. Сообщение администратору уже отправлено")
                logging.error(f"Ошибка при генерации изображения у пользователя {message.from_user.id}: {e}")
        else:
            delete_message = await message.answer("Пожалуйста, введите текст запроса после команды /img.")
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Админстратор не дал вам доступ! {Emojis.ALLERT}\nПодождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    
    if load_message: await bot.delete_message(chat_id=message.chat.id, message_id=load_message.message_id)
    if delete_message: await state.update_data(message_id=delete_message.message_id)
    
    if message_log: await send_log_message(message, bot, message_log)
    
    