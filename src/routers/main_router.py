# -*- coding: UTF-8 -*-

import logging
import time

from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.enums import ParseMode
from aiogram import Router, F, Bot
from aiogram.types import Message

from openai import AsyncOpenAI, APIStatusError

import tiktoken

from admin.admin_logs import send_log_message

from models.emojis import Emojis

from services.postgres.role_management_service import RoleManagmentService
from services.postgres.user_service import UserService
from services.postgres.group_service import GroupService

from utils.assistant import MinorOperations

from exceptions.errors import UserNotRegError, AccessDeniedError

router = Router()


@router.message(F.text.not_in(['/start', '/control', '/cancel', '/balance', '/view_set_options', '/role_options','/change_models', '/change_api_key', '/tariffs', '/help']) & ~F.text.contains('/img'), StateFilter(None))
async def handle_user_request(message: Message, state: FSMContext, bot: Bot):
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    SUPER_GROUP_ID = await GroupService.get_group_id()
    if message.chat.id== SUPER_GROUP_ID:
        return 
    await state.clear()
    await send_log_message(message, bot, message)
    message_log = False
    delete_message = False
    try:
        await UserService.check_user_rights(message.from_user.id)
        primary_balance = await MinorOperations.check_balance(message.from_user.id)
        openai_api_key = await UserService.get_user_data(message.from_user.id, 'encrypted_api_account_key')
        
        temporary_user_data = await RoleManagmentService.get_temporary_user_data(message.from_user.id, 'all')
        temporary_user_data.history_dialog.append({
                    "role": "user",
                    "content": f"{message.text}"
                })
        encoding = tiktoken.encoding_for_model(temporary_user_data.llm_model)  # Замените на вашу модель
        total_tokens = 0
        load_message = await message.answer(f'{Emojis.TIME} Обработка запроса')
        try:
            client = AsyncOpenAI(api_key=openai_api_key, base_url="https://api.proxyapi.ru/openai/v1")
            stream = await client.chat.completions.create(
                messages=temporary_user_data.history_dialog,
                model=temporary_user_data.llm_model,
                temperature=0.5,
                max_completion_tokens=2048,
                stream=True
            )
            answer_message = await bot.edit_message_text(chat_id=load_message.chat.id, message_id=load_message.message_id, text="Печатает... 0 сек")
            message_response = "Ответ:\n\n"
            next_part_message = ''
            start_time = time.time()
            printing_time = 0
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0 and  not chunk.choices[0].finish_reason:
                    next_part_message += chunk.choices[0].delta.content
                    tokens_in_chunk = len(encoding.encode(next_part_message))
                    total_tokens += tokens_in_chunk
                    if len(next_part_message) >= 400:
                        message_response += next_part_message
                        next_part_message = ''
                        printing_time = time.time() - start_time
                        await bot.edit_message_text(chat_id=answer_message.chat.id, message_id=answer_message.message_id, text=message_response + f"\nПечатает... {int(printing_time)} сек.")
                else:
                    break
            message_response += next_part_message
            message_response = message_response.replace("Ответ:\n\n", "")
            printing_time = time.time() - start_time
            secondary_balance = await MinorOperations.check_balance(message.from_user.id)
            temporary_user_data.history_dialog.append({
                        "role": "assistant",
                        "content": f"{message_response}"
                    })
            message_log = await bot.edit_message_text(chat_id=answer_message.chat.id, message_id=answer_message.message_id, text=message_response + f"\n\n Затраты: {round(primary_balance-secondary_balance, 3)} рублей", parse_mode=ParseMode.MARKDOWN)
            await RoleManagmentService.update_dialog_history(message.from_user.id, temporary_user_data.name_role, temporary_user_data.history_dialog)
        except APIStatusError as e:
                error_detail = e.response.json()
                if "Insufficient balance" in error_detail.get('detail'):
                    message_log = await bot.edit_message_text(chat_id=load_message.chat.id, message_id=load_message.message_id, text=f"{Emojis.FAIL} Недостаточно средств для совершения операции! {Emojis.FAIL}\n\n Текущий баланс: {primary_balance} рублей\n\nОчистите историю роли или пополните баланс в личном кабинете.")
                    logging.error(f"Маленький баланс у пользователя {message.from_user.id}: {e}")
                elif "Invalid API Key" in error_detail.get('detail'):
                    message_log = await bot.edit_message_text(chat_id=load_message.chat.id, message_id=load_message.message_id, text=f"{Emojis.FAIL} Неверный API ключ! {Emojis.FAIL}\n\nЧтобы поменять введите /change_api_key")
                    logging.error(f"Неверный API ключ у пользователя {message.from_user.id}: {e}")
                else:
                    message_log = await bot.edit_message_text(chat_id=load_message.chat.id, message_id=load_message.message_id, text="Извините, произошла ошибка. Сообщение администратору уже отправлено")
                    logging.error(f"Ошибка при генерации изображения у пользователя {message.from_user.id}: {e}")
        except Exception as e:
            message_log = await message.answer("Извините, произошла ошибка. Сообщение администратору уже отправлено")
            logging.error(f"Ошибка при запросе к LLM у пользователя {message.from_user.id}: {e}")
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start")
    except AccessDeniedError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Админстратор не дал вам доступ! {Emojis.ALLERT}\nПодождите пока вам придет уведомление о том что доступ разрешен")
    
    if delete_message: await state.update_data(message_id=delete_message.message_id)
    
    if message_log: await send_log_message(message, bot, message_log)