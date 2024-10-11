# -*- coding: UTF-8 -*-
import json 

from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Router, Bot

from models.user_keyboards import UserKeyboards
from models.emojis import Emojis

from services.postgres.user_service import UserService
from services.postgres.role_management_service import RoleManagmentService

from exceptions.errors import UserNotRegError, AccessDeniedError

router = Router()


@router.message(Command(commands=['change_models']))
async def change_model(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Выввод клавиатуры с моделями
    """
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    await state.clear()
    try:
        await UserService.check_user_rights(message.from_user.id)
        ai_models_keyboard = await UserKeyboards.ai_models_keyboard(message.from_user.id)
        delete_message = await message.answer("Выберите модель:", reply_markup=ai_models_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
        
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer("Админстратор не дал вам доступ. Подождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    await state.update_data(message_id=delete_message.message_id)
    


    
@router.callback_query(lambda F: 'change_llm_model' in F.data or 'change_img_model' in F.data)
async def change_llm_or_img_model(callback: CallbackQuery, bot: Bot) -> None:
    """
    Смена языковой или генеративной модели
    """
    data = json.loads(callback.data)
    
    temporary_user_data = await RoleManagmentService.get_temporary_user_data(callback.from_user.id, 'all_ids')
    
    if data['key'] == 'change_llm_model':
        if data['value'] == temporary_user_data.llm_model_id:
            await callback.answer(text='Данная модель уже выбрана', show_alert=True)
        else:
            await RoleManagmentService.set_model_options(callback.from_user.id, 'llm_model_id', data['value'])
            
            ai_models_keyboard = await UserKeyboards.ai_models_keyboard(callback.from_user.id)
            await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=ai_models_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    elif data['key'] == 'change_img_model':
        await RoleManagmentService.set_model_options(callback.from_user.id, 'img_model_id', data['value'])
        
        quality_img_models_keyboard = await UserKeyboards.quality_img_models_keyboard(callback.from_user.id)
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Выберите качество генерируемого изображения:', reply_markup=quality_img_models_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    await callback.answer()
    
    
@router.callback_query(lambda F: 'change_quality' in F.data)
async def change_quality_img_model(callback: CallbackQuery, bot: Bot) -> None:
    """
    Смена качества для генеративной модели
    """
    data = json.loads(callback.data)
    
    temporary_user_data = await RoleManagmentService.get_temporary_user_data(callback.from_user.id, 'all_ids')
    
    if data['key'] == 'change_quality':
        if data['value'] == temporary_user_data.quality_generated_image:
            await callback.answer(text='Данное качество изображения уже выбрано', show_alert=True)
        else:
            await RoleManagmentService.set_model_options(callback.from_user.id, 'quality_generated_image', data['value'])
            
            ai_models_keyboard = await UserKeyboards.ai_models_keyboard(callback.from_user.id)
            await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Выберите модель", reply_markup=ai_models_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    await callback.answer('Качество генерируемого изображения успешно изменено')