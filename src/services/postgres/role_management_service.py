# -*- coding: UTF-8 -*-
from typing import Union
import logging

from collections import namedtuple

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, func, update, delete, join

from models.table_models.temporary_dialog_data import TemporaryDialogData
from models.table_models.model_roles import ModelRole
from models.table_models.llm_models import LlmModel
from models.table_models.img_models import ImgModel
from models.table_models.user import User

from services.postgres.database import get_async_session

from exceptions.errors import  RegistrationError, ActiveRoleDeletionError

from config import CIPHER_SUITE

class RoleManagmentService:
    def __init__(self):
        pass


    @staticmethod
    async def get_temporary_user_data(user_id: int, type_data: str) -> TemporaryDialogData:
        """
            Получение настроек пользователя
            type_data: 'all' - Получение полных данных
            type_data: 'fio' - Получение только ссфлок на данные
            
        Args:
            user_id (int): User Telegram ID
            type_data (str): Type data requested

        Returns:
            TemporaryDialogData: User model settings
        """
        async for session in get_async_session():
            try:
                match type_data:
                    case 'all':
                        full_dialog_info_query = await session.execute(
                            select(
                                TemporaryDialogData.id,
                                TemporaryDialogData.id_tg,
                                ModelRole.name_role.label('name_role'),
                                ModelRole.history_dialog.label('history_dialog'),
                                LlmModel.value.label('llm_model'),
                                ImgModel.value.label('img_model'),
                                TemporaryDialogData.quality_generated_image
                            )
                            .where(TemporaryDialogData.id_tg == user_id)
                            .select_from(
                                join(TemporaryDialogData, LlmModel, TemporaryDialogData.llm_model_id == LlmModel.id)
                                .join(ImgModel, TemporaryDialogData.img_model_id == ImgModel.id)
                                .join(ModelRole, TemporaryDialogData.role_id == ModelRole.id)   
                            )
                        )
                        full_data = full_dialog_info_query.one()
                        
                        return full_data
                    case 'all_ids':
                        dialog_ids_query = await session.execute(
                            select(TemporaryDialogData)
                            .where(TemporaryDialogData.id_tg == user_id)
                        )
                        ids_data = dialog_ids_query.scalar()
                        
                        return ids_data
                    case _:
                        data_mapping = {
                            'fio': ids_data.fio,
                            'phone_number': ids_data.phone_number,
                            'encrypted_api_account_key': CIPHER_SUITE.decrypt(ids_data.encrypted_api_account_key).decode('utf-8') 
                        }
                        return data_mapping.get(type_data)
            except SQLAlchemyError as e:
                logging.error(f"Ошибка получения настроек пользователя с id_tg {user_id}: {e}")
                
    
    @staticmethod
    async def set_model_options(user_id: int, type_data: str, insert_value: Union[str, dict, list]) -> None:
        """
            Сохранение настроек
        Args:
            user_id (int): User Telegram ID
            type_data (str): Stored data type
            insert_value (Union[str, dict, list]): Stored data value
        """
        async for session in get_async_session():
            try:
                values_to_update = {}
                values_to_update[type_data] = insert_value

                await session.execute(
                    update(TemporaryDialogData)
                    .where(TemporaryDialogData.id_tg == user_id)
                    .values(**values_to_update)
                )
                await session.commit()
            except SQLAlchemyError as e:
                logging.error(f"Ошибка сохранения \'{type_data}\' для пользователя с id_tg {user_id}: {e}")
                
                
    @staticmethod
    async def get_user_model_roles(user_id: int) -> ModelRole:
        """
            Получение всех ролей для LLM моделей пользователя

        Args:
            user_id (int): User Telegram ID

        Returns:
            ModelRole: User Model roles
        """
        async for session in get_async_session():
            try:

                get_user_roles_query = await session.execute(
                    select(
                        ModelRole.id,
                        User.id_tg.label('owner_id_tg'),
                        ModelRole.name_role,
                        ModelRole.history_dialog
                    )
                    .select_from(
                        join(ModelRole, User, ModelRole.owner_id == User.id)
                    )
                    .where(User.id_tg == user_id)
                )
                UserRole = namedtuple('UserRole', ['id', 'owner_id_tg', 'name_role', 'history_dialog'])

                user_roles = [UserRole(*row) for row in get_user_roles_query.fetchall()]
                
                return user_roles
            except SQLAlchemyError as e:
                logging.error(f"Ошибка получения ролей пользователя с id_tg {user_id}: {e}")
        
    
    @staticmethod
    async def create_role(user_id: int, name_role: str, context: dict) -> int:
        """
            Создание новой роли

        Args:
            user_id (int): User Telegram ID
            name_role (str): Name new role
            context (dict): New role system promt

        Returns:
            int: New role ID
        """
        system_promt = [
            {"role": "system", "content": context}
        ]
        async for session in get_async_session():
            try:
                get_user_id_query = await session.execute(
                    select(User.id)
                    .where(User.id_tg == user_id)
                )
                user_id = get_user_id_query.scalar()
                
                new_role = ModelRole(
                    owner_id=user_id,
                    name_role=name_role,
                    history_dialog=system_promt
                )
                
                session.add(new_role)
                await session.commit()
                
                return new_role.id
            except SQLAlchemyError as e:
                logging.error(f"Ошибка создания роли для пользователя с id_tg {user_id}: {e}")
 


    @staticmethod
    async def update_dialog_history(user_id: int, name_role: str,  history_dialog: list) -> None:
        """
            Обновление истории диалога для роли

        Args:
            user_id (int): User telegram ID
            name_role (str): Name updated role
            history_dialog (list): Updated history dialog
        """
        async for session in get_async_session():
            try:
                get_owner_id_query = await session.execute(
                    select(User.id)
                    .where(User.id_tg == user_id)
                )
                owner_id = get_owner_id_query.scalar()
                
                await session.execute(
                    update(ModelRole)
                    .where(
                        ModelRole.owner_id == owner_id,
                        ModelRole.name_role == name_role,
                    )
                    .values(
                        history_dialog=history_dialog
                    )
                )
                await session.commit()
            except SQLAlchemyError as e:
                logging.error(f"Ошибка обновления истории роли у пользователя с id_tg {user_id}: {e}")


    @staticmethod
    async def clear_role_dialog_history(role_id: int) -> None:
        """
            Очищение истории роли

        Args:
            role_id (int): ID cleared role

        """
        async for session in get_async_session():
            try:
                get_role_history_dialog = await session.execute(
                    select(ModelRole.history_dialog)
                    .where(ModelRole.id == role_id)
                )
                history_dialog = get_role_history_dialog.scalar()
                clear_history_dialog = [history_dialog[0]]
                await session.execute(
                    update(ModelRole)
                    .where(
                        ModelRole.id == role_id,
                    )
                    .values(
                        history_dialog=clear_history_dialog
                    )
                )
                await session.commit()
            except SQLAlchemyError as e:
                logging.error(f"Ошибка удалениия истории у роли {role_id}: {e}")


    @staticmethod
    async def delete_role(role_id: int) -> None:
        """
        Удаление роли

        Args:
            role_id (int): Role ID to be deleted

        Raises:
            ActiveRoleDeletionError: Role ID to be deleted is active
        """
        async for session in get_async_session():
            try:
                await session.execute(
                    delete(ModelRole)
                    .where(ModelRole.id == role_id)
                )
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                logging.error(f"Попытка удалить активную роль: {e}")
                raise ActiveRoleDeletionError
            except SQLAlchemyError as e:
                logging.error(f"Ошибка удаления роли: {e}")
    
    
    
    @staticmethod
    async def change_system_promt_role(role_id: int, new_system_promt: str) -> None:
        """
        Изменение контекста роли

        Args:
            role_id (int): Role ID to be changed
            new_system_promt (str): New system promt for role
        """
        async for session in get_async_session():
            try:
                get_role_history_dialog = await session.execute(
                    select(ModelRole.history_dialog)
                    .where(ModelRole.id == role_id)
                )
                history_dialog = get_role_history_dialog.scalar()
                history_dialog[0]['content'] = new_system_promt
                await session.execute(
                    update(ModelRole)
                    .where(
                        ModelRole.id == role_id,
                    )
                    .values(
                        history_dialog=history_dialog
                    )
                )
                await session.commit()
            except SQLAlchemyError as e:
                logging.error(f"Ошибка: {e}")


    @staticmethod
    async def set_default_model_options(user_id: int) -> None:
        """
            Настройка стандартных опций для пользователя
        
        Args:
            user_id (int): User telegram ID

        Raises:
            RegistrationError: Registration error
        """

        async for session in get_async_session():
            try:
                user_exists_query = await session.execute(
                    select(func.count('*'))
                    .where(TemporaryDialogData.id_tg == user_id)
                )
                user_exists_flag = user_exists_query.scalar()
                
                get_llm_model_id = await session.execute(
                    select(LlmModel)
                    .where(LlmModel.value == 'gpt-4o-mini')
                )
                llm_model_id = get_llm_model_id.scalar()
                
                get_img_model_id = await session.execute(
                    select(ImgModel)
                    .where(ImgModel.value == 'dall-e-2')
                )
                img_model_id = get_img_model_id.scalar()
                role_id = await RoleManagmentService.create_role(user_id, 'Универсальный помощник', "Вы — универсальный помощник, способный предоставлять информацию и помощь по широкому спектру тем.")
                
                if not user_exists_flag:
                    set_defaut_settings = TemporaryDialogData(
                        id_tg=user_id,
                        role_id=role_id,
                        llm_model_id=llm_model_id.id,
                        img_model_id=img_model_id.id,
                        quality_generated_image='1024x1024'
                    )
                    
                    session.add(set_defaut_settings)
                    await session.commit()
                
            except SQLAlchemyError as e:
                logging.error(f"Ошибка настройки пользователя: {e}")
                raise RegistrationError from e