# -*- coding: UTF-8 -*-

from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import StateFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import Router, F, Bot

from admin.admin_logs import send_log_message

from services.postgres.role_management_service import RoleManagmentService
from services.postgres.group_service import GroupService
from services.postgres.user_service import UserService


from models.user_keyboards import UserKeyboards
from models.states import RegUserStates
from models.emojis import Emojis

from exceptions.errors import UserNotRegError, RegistrationError, AccessDeniedError, TelegramAddressNotValidError

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Начало регистрации
    """
    if (await state.get_data()).get('message_id'):
        await bot.delete_message(chat_id=message.chat.id, message_id=(await state.get_data()).get('message_id'))
    await state.clear()
    try:
        user_date_reg =  await UserService.check_user_rights(message.from_user.id)
        await message.answer((f"Вы уже зарегистрированы!\nДата регистрации: {user_date_reg.strftime('%d.%m.%Y %H:%M')}"))
    except UserNotRegError:
        await UserService.init_user(message.from_user.id)
        delete_message = await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
        await state.update_data(message_id=delete_message.message_id)
        await state.set_state(RegUserStates.get_fio)
    except AccessDeniedError:
        delete_message = await message.answer("Вы зарегистрированы, но Админстратор не дал вам доступ к работе бота. Подождите пока вам придет уведомление о том  что  доступ разрешен", reply_markup=ReplyKeyboardRemove())
        await state.clear()


@router.message(F.text, StateFilter(RegUserStates.get_fio))
async def get_fio(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получение и сохранение ФИО пользователя
    """
    await bot.delete_message(chat_id=message.chat.id, message_id=(await state.get_data()).get('message_id'))
    await UserService.save_data(message.from_user.id, 'fio', message.text)
    
    phone_access_request_keyboard = await UserKeyboards.phone_access_request()
    delete_message = await message.answer("Отправьте свой номер телефона нажав на кнопку ниже", reply_markup=phone_access_request_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    
    await state.update_data(message_id=delete_message.message_id)
    await state.set_state(RegUserStates.get_phone_number)
    

@router.message(F.contact | F.text, StateFilter(RegUserStates.get_phone_number))
async def get_phone_number(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получение и сохранение номер телефона
    """
    await bot.delete_message(chat_id=message.chat.id, message_id=(await state.get_data()).get('message_id'))
    if message.text == 'Вернуться назад':
        delete_message = await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
        
        await state.set_state(RegUserStates.get_fio)
    elif message.contact:
        await UserService.save_data(message.from_user.id, 'phone_number', message.contact.phone_number)
        delete_message = await message.answer("Отправьте API ключ для вашего аккаунта:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(RegUserStates.get_api_key)
    else:
        phone_access_request_keyboard = await UserKeyboards.phone_access_request()
        delete_message = await message.answer("Отправьте свой номер телефона нажав на кнопку ниже", reply_markup=phone_access_request_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
    
    await state.update_data(message_id=delete_message.message_id)
        
        
@router.message(F.text, StateFilter(RegUserStates.get_api_key))
async def get_api_key(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получение API ключа и завершение регистрации
    """
    SUPER_GROUP_ID = await GroupService.get_group_id()
    message_log = False
    try:
        await UserService.reg_user(message.from_user.id, message.from_user.username, message.from_user.full_name, message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=(await state.get_data()).get('message_id'))
        
        new_topic = await bot.create_forum_topic(chat_id=SUPER_GROUP_ID, name=message.from_user.full_name)
        await GroupService.save_user_message_thread_id(message.from_user.id, new_topic.message_thread_id)
        
        user_data = await UserService.get_user_data(message.from_user.id, 'all')

        access_keyboard = await UserKeyboards.bot_access_request(message.from_user.id)
        new_user_message = await bot.send_message(chat_id=SUPER_GROUP_ID, text=f'ID пользователя: {message.from_user.id}\nТелеграмм имя пользователя: {message.from_user.full_name}\nАдрес пользователя: @{message.from_user.username}\nФИО: {user_data.fio}\nТелефон: {user_data.phone_number}\nID темы: {new_topic.message_thread_id}', reply_to_message_id=new_topic.message_thread_id, reply_markup=access_keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True))
        await bot.pin_chat_message(chat_id=SUPER_GROUP_ID, message_id=new_user_message.message_id)
        await RoleManagmentService.set_default_model_options(message.from_user.id)
        
        await message.answer(f"{Emojis.SUCCESS} Поздравляю! Вы успешно прошли регистрацию! {Emojis.SUCCESS}\n\nДождитесь подтверждения вашего доступа")
    except TelegramAddressNotValidError:
        message_log = await message.answer(f"{Emojis.FAIL} Ошибка регистрации! {Emojis.FAIL}\n\nУ вас пустой адрес телеграмм аккаунта. Для успешной регистрации он не должен быть пустым. Если вы не знаете как его поменять обратитесь в поддержку по адресу @global_aide_bot.")
    except RegistrationError:
        message_log = await message.answer(f"{Emojis.FAIL} Ошибка регистрации! {Emojis.FAIL}")
    await state.clear()
    if message_log: await send_log_message(message, bot, message_log)