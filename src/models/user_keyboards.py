# -*- coding: UTF-8 -*-

import json

from aiogram.utils.keyboard import KeyboardButton, InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from models.emojis import Emojis
from services.postgres.admin_service import AdminService
from services.postgres.role_management_service import RoleManagmentService

class UserKeyboards:
    def __init__(self) -> None:
        pass
    
    
    @staticmethod
    async def phone_access_request() -> ReplyKeyboardBuilder:
        """
        Клавиатура для отправки телефона при регистрации
        """
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Вернуться назад"))
        builder.row(KeyboardButton(text="Отправить номер телефона", request_contact=True))
        
        return builder
    
    
    @staticmethod
    async def bot_access_request(user_id: int) -> InlineKeyboardBuilder:
        """
        Клавиатура управления доступом пользователей
        """
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Разрешить доступ", callback_data=json.dumps({'key': 'allow_access', 'value': user_id})))
        builder.row(InlineKeyboardButton(text="Временно ограничить доступ", callback_data=json.dumps({'key': 'temporarily_restrict_access', 'value': user_id})))
        builder.row(InlineKeyboardButton(text="Запретить доступ", callback_data=json.dumps({'key': 'deny_access', 'value': user_id})))
        
        return builder
    
    
    @staticmethod
    async def ai_models_keyboard(user_id: int) -> InlineKeyboardBuilder:
        """
        Клавитаура выбора LLM и генеративных моделей
        """
        builder = InlineKeyboardBuilder()
        
        llm_models = await AdminService.get_table('llm_models')
        img_models = await AdminService.get_table('img_models')
        temporary_user_data = await RoleManagmentService.get_temporary_user_data(user_id, 'all_ids')
        
        builder.row(InlineKeyboardButton(text="Языковые модели", callback_data=json.dumps({'key': None})))
        buttons = []
        
        for model in llm_models:
            if model.id == temporary_user_data.llm_model_id:
                buttons.append(InlineKeyboardButton(text=f"{Emojis.SUCCESS} {model.name}", callback_data=json.dumps({'key': 'change_llm_model', 'value': model.id})))
            else:
                buttons.append(InlineKeyboardButton(text=f"{model.name}", callback_data=json.dumps({'key': 'change_llm_model', 'value': model.id})))
            if len(buttons) == 2:
                builder.row(*buttons)
                buttons = []
        builder.row(*buttons)
        
        builder.row(InlineKeyboardButton(text="Генеративные модели", callback_data=json.dumps({'key': None})))
        buttons = []
        
        for model in img_models:
            if model.id == temporary_user_data.img_model_id:
                buttons.append(InlineKeyboardButton(text=f"{Emojis.SUCCESS} {model.name}", callback_data=json.dumps({'key': 'change_img_model', 'value': model.id})))
            else:
                buttons.append(InlineKeyboardButton(text=f"{model.name}", callback_data=json.dumps({'key': 'change_img_model', 'value': model.id})))
            if len(buttons) == 2:
                builder.row(*buttons)
                buttons = []
        
        builder.row(*buttons)
        return builder
    
    @staticmethod
    async def quality_img_models_keyboard(user_id: int) -> InlineKeyboardBuilder:
        """
        Клавиатура качества генерируемого изображения 
        """
        builder = InlineKeyboardBuilder()
        
        temporary_user_data = await RoleManagmentService.get_temporary_user_data(user_id, 'all')
        
        dalle_2_quality_map = ['256x256', '512x512', '1024x1024']
        dalle_3_quality_map = ['1024x1024', '1792x1024', '1024x1792']
        
        if temporary_user_data.img_model == 'dall-e-2':
            selected_model_quality_map = dalle_2_quality_map
        else:
            selected_model_quality_map = dalle_3_quality_map
        
        buttons = []
        
        for quality in selected_model_quality_map:
            if quality == temporary_user_data.quality_generated_image:
                buttons.append(InlineKeyboardButton(text=f"{Emojis.SUCCESS} {quality}", callback_data=json.dumps({'key': 'change_quality', 'value': quality})))
            else:
                buttons.append(InlineKeyboardButton(text=f"{quality}", callback_data=json.dumps({'key': 'change_quality', 'value': quality})))
        builder.row(*buttons)
        
        return builder
    
        
    @staticmethod
    async def ai_model_roles_keyboard(user_id: int) -> InlineKeyboardBuilder:
        """
        Клавиатура ролей для моделей
        """
        builder = InlineKeyboardBuilder()
        temporary_user_data = await RoleManagmentService.get_temporary_user_data(user_id, 'all_ids')
        user_roles = await RoleManagmentService.get_user_model_roles(user_id)
        
        for role in user_roles:
            if role.id == temporary_user_data.role_id:
                builder.row(InlineKeyboardButton(text=f"{Emojis.SUCCESS} {role.name_role}", callback_data=json.dumps({'key': 'customise_role', 'value': role.id})))
            else:
                builder.row(InlineKeyboardButton(text=f"{role.name_role}", callback_data=json.dumps({'key': 'customise_role', 'value': role.id})))
                
        builder.row(InlineKeyboardButton(text="Добавить новую роль", callback_data=json.dumps({'key': 'create_role'})))
        return builder
    
    
    @staticmethod
    async def role_options_keyboard(role_id: int) -> InlineKeyboardBuilder:
        """
        Клавиатура управления ролью
        """
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Выбрать", callback_data=json.dumps({'key': 'change_model_role', 'value': role_id})))
        builder.row(InlineKeyboardButton(text="Изменить контекст", callback_data=json.dumps({'key': 'change_system_promt', 'value': role_id})))
        builder.row(InlineKeyboardButton(text="Очистить историю", callback_data=json.dumps({'key': 'clear_dialog_history', 'value': role_id})))
        builder.row(InlineKeyboardButton(text="Удалить", callback_data=json.dumps({'key': 'delete_role', 'value': role_id})))
        builder.row(InlineKeyboardButton(text="Вернуться назад", callback_data=json.dumps({'key': 'back_to_roles'})))
        return builder