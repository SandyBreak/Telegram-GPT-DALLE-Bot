# -*- coding: UTF-8 -*-

import logging
import json

from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram import Router, Bot, F


from models.states import CreateRoleStates, ChangeSystemPromt
from models.user_keyboards import UserKeyboards
from models.emojis import Emojis

from services.postgres.role_management_service import RoleManagmentService
from services.postgres.admin_service import AdminService
from services.postgres.user_service import UserService

from exceptions.errors import UserNotRegError, AccessDeniedError, ActiveRoleDeletionError

router = Router()


@router.message(Command(commands=['role_options']))
async def change_role(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    await state.clear()
    try:
        await UserService.check_user_rights(message.from_user.id)
        
        ai_model_roles_keyboard = await UserKeyboards.ai_model_roles_keyboard(message.from_user.id)
        delete_message = await message.answer("Выберите роль:", reply_markup=ai_model_roles_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    except UserNotRegError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Вы не зарегистрированы! {Emojis.ALLERT}\nДля регистрации введите команду /start", reply_markup=ReplyKeyboardRemove())
    except AccessDeniedError:
        delete_message = await message.answer(f"{Emojis.ALLERT} Админстратор не дал вам доступ! {Emojis.ALLERT}\nПодождите пока вам придет уведомление о том что доступ разрешен", reply_markup=ReplyKeyboardRemove())
    await state.update_data(message_id=delete_message.message_id)




@router.callback_query(lambda F: 'create_role' in F.data)
async def create_role(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    user_roles = await RoleManagmentService.get_user_model_roles(callback.from_user.id)
    if len(user_roles)>= 5:
        await callback.answer(f"У вас максимально количество ролей: {len(user_roles)}", show_alert=True)    
    else:
        delete_message = await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Введите имя роли:")
        await state.update_data(message_id=delete_message.message_id)
        await state.set_state(CreateRoleStates.get_name)


@router.message(F.text, StateFilter(CreateRoleStates.get_name))
async def get_name(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    
    if len(message.text) > 128:
        await message.answer("Слишком длинное имя! имя роли не должно быть длиннее 128 символов")
    else:
        delete_message = await message.answer("Введите контекст роли, например: \"Ты высоко-квалифицированный врач в области кардио-хирургии\"")
        
        await state.update_data(message_id=delete_message.message_id, name_role=message.text)
        await state.set_state(CreateRoleStates.get_system_promt_and_create_role)

@router.message(F.text, StateFilter(CreateRoleStates.get_system_promt_and_create_role))
async def get_system_promt_and_create_role(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)
    
    name_role = (await state.get_data()).get('name_role')
    
    try:
        await RoleManagmentService.create_role(message.from_user.id, name_role, message.text)
        ai_model_roles_keyboard = await UserKeyboards.ai_model_roles_keyboard(message.from_user.id)
        delete_message = await message.answer("Выберите роль:", reply_markup=ai_model_roles_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    except Exception as e:
        logging.error(f'Ошибка создания роли: {e}')
        delete_message = await message.answer(f"{Emojis.FAIL} Ошибка создания роли! {Emojis.FAIL}", reply_markup=ReplyKeyboardRemove())
    
    await state.clear()
    



@router.callback_query(lambda F: 'customise_role' in F.data)
async def customise_role(callback: CallbackQuery, bot: Bot) -> None:
    data = json.loads(callback.data)
    all_roles = await AdminService.get_table('model_roles')
    if data['key'] == 'customise_role':
        for role in all_roles:
            if role.id == data['value']:
                role_name = role.name_role
                break
        role_options_keyboard = await UserKeyboards.role_options_keyboard(data['value'])
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=f"Настройка роли \"{role_name}\"", reply_markup=role_options_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    await callback.answer()
    
    


@router.callback_query(lambda F: 'change_model_role' in F.data)
async def change_model_role(callback: CallbackQuery, bot: Bot) -> None:
    data = json.loads(callback.data)
    temporary_user_data = await RoleManagmentService.get_temporary_user_data(callback.from_user.id, 'all_ids')
    if data['key'] == 'change_model_role':
        if data['value'] == temporary_user_data.role_id:
            await callback.answer(text='Данная роль уже выбрана', show_alert=True)
        else:
            await RoleManagmentService.set_model_options(callback.from_user.id, 'role_id', data['value'])
            ai_model_roles_keyboard = await UserKeyboards.ai_model_roles_keyboard(callback.from_user.id)
        
            await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Выберите роль:', reply_markup=ai_model_roles_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))




@router.callback_query(lambda F: 'change_system_promt' in F.data)
async def change_system_promt(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    delete_message = await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Введите новый контекст роли:")
    data = json.loads(callback.data)
    
    await state.update_data(message_id=delete_message.message_id, role_id=data['value'])
    await state.set_state(ChangeSystemPromt.get_and_change_system_promt)
    

@router.message(F.text, StateFilter(ChangeSystemPromt.get_and_change_system_promt))
async def get_and_change_system_promt(message: Message, state: FSMContext, bot: Bot) -> None:
    if (delete_message_id := (await state.get_data()).get('message_id')): await bot.delete_message(chat_id=message.chat.id, message_id=delete_message_id)

    role_id = (await state.get_data()).get('role_id')
    try:
        await RoleManagmentService.change_system_promt_role(role_id, message.text)
        ai_model_roles_keyboard = await UserKeyboards.ai_model_roles_keyboard(message.from_user.id)
        delete_message = await message.answer("Выберите роль:", reply_markup=ai_model_roles_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    except Exception as e:
        logging.error(f'Ошибка изменения контекста: {e}')
        delete_message = await message.answer(f"{Emojis.FAIL} Ошибка изменения контекста! {Emojis.FAIL}")
        
        await state.update_data(message_id=delete_message.message_id, name_role=message.text)
        await state.set_state(CreateRoleStates.get_system_promt_and_create_role)

    await state.clear()




    
@router.callback_query(lambda F: 'clear_dialog_history' in F.data)
async def clear_dialog_history(callback: CallbackQuery) -> None:
    data = json.loads(callback.data)
    if data['key'] == 'clear_dialog_history':
        await RoleManagmentService.clear_role_dialog_history(data['value'])
    await callback.answer("История роли удалена", show_alert=True)
    



@router.callback_query(lambda F: 'delete_role' in F.data)
async def delete_role(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = json.loads(callback.data)
    if data['key'] == 'delete_role':
        try:
            await RoleManagmentService.delete_role(data['value'])
            ai_model_roles_keyboard = await UserKeyboards.ai_model_roles_keyboard(callback.from_user.id)
            delete_message = await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Выберите роль:", reply_markup=ai_model_roles_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    
            await state.update_data(message_id=delete_message.message_id)
        except ActiveRoleDeletionError:    
            await callback.answer("Нельзя удалить роль которая используется. Выберите другую роль, а потом удалите эту.", show_alert=True)
     
    
    
    
@router.callback_query(lambda F: 'back_to_roles' in F.data)
async def back_to_roles(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    ai_model_roles_keyboard = await UserKeyboards.ai_model_roles_keyboard(callback.from_user.id)
    delete_message = await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="Выберите роль:", reply_markup=ai_model_roles_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    
    await state.update_data(message_id=delete_message.message_id)