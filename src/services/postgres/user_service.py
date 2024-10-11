# -*- coding: UTF-8 -*-

from typing import Optional, Union
from datetime import datetime
import logging

from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models.table_models.user import User

from services.postgres.database import get_async_session

from exceptions.errors import UserNotRegError, RegistrationError, AccessDeniedError, TelegramAddressNotValidError
from config import CIPHER_SUITE

class UserService:
    def __init__(self):
        pass
    
    
    @staticmethod
    async def check_user_rights(user_id: int) -> Optional[datetime]:
        """
        Проверка зарегистирован пользователь или нет и статуса его доступа 
        """
        async for session in get_async_session():
            try:
                check_user_date_reg = await session.execute(select(User).where(User.id_tg == user_id))
                user_data = check_user_date_reg.scalar()
                if user_data:
                    if user_data.date_reg:
                        if user_data.access_flag:
                            return user_data.date_reg
                        else:
                            raise AccessDeniedError
                    else:
                        raise UserNotRegError
                else:
                    raise UserNotRegError
            except SQLAlchemyError as e:
                logging.error(f"Ошибка проверки доступа пользователя с id_tg {user_id}: {e}")
                raise e
    
    
    @staticmethod
    async def init_user(user_id: int) -> None:
        """
        Инициализация пользователя, сохранение:
            1. ID Аккаунта
        """
        async for session in get_async_session():
            try:
                user_exists_query = await session.execute(
                    select(func.count('*'))
                    .where(User.id_tg == user_id)
                )
                user_exists_flag = user_exists_query.scalar()
                
                if not user_exists_flag:
                    new_user = User(
                        id_tg=user_id,
                    )

                    # Выполнение вставки
                    session.add(new_user)
                    await session.commit()
                
            except SQLAlchemyError as e:
                logging.error(f"Ошибка инициализации пользователя с id_tg {user_id}: {e}")
                raise RegistrationError from e
    

    @staticmethod
    async def reg_user(user_id: int, nickname: str, full_name: str, api_account_key: str) -> None:
        """
        Регистрация пользователя, сохранение:
            1. Адреса телеграмм аккаунта
            2. Имени телеграмм аккаунта
            3. API Ключа
            4. Даты регистрации
            5. Отрицательного флага доступа 
        """
        async for session in get_async_session():
            try:
                await session.execute(
                    update(User)
                    .where(User.id_tg == user_id)
                    .values(
                        nickname=nickname,
                        fullname=full_name,
                        encrypted_api_account_key=CIPHER_SUITE.encrypt(api_account_key.encode('utf-8')),
                        date_reg=datetime.now(),
                        access_flag=False
                    )
                )
                await session.commit()
            except IntegrityError as e:
                logging.error(f"Пустой адрес аккаунта у пользователя с id_tg {user_id}: {e}")
                raise TelegramAddressNotValidError
            except SQLAlchemyError as e:
                logging.error(f"Ошибка регистрации пользователя с id_tg {user_id}: {e}")
                raise RegistrationError from e
    
    
    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        Удаление пользователя из базы данных
        """
        async for session in get_async_session():
            try:
                await session.execute(
                    delete(User)
                    .where(User.id_tg == user_id)
                )
                await session.commit()
            except SQLAlchemyError as e:
                logging.error(f"Ошибка удаления пользователя с id_tg {user_id}: {e}")
    
    
    @staticmethod
    async def save_data(user_id: int, type_data: str, insert_value: Union[str, bool, bytes]) -> None:
        """
        Сохранение данных о пользователе
        """
        async for session in get_async_session():
            try:
                values_to_update = {}
                values_to_update[type_data] = insert_value

                await session.execute(
                    update(User)
                    .where(User.id_tg == user_id)
                    .values(**values_to_update)
                )
                await session.commit()
            except SQLAlchemyError as e:
                logging.error(f"Ошибка сохранения '{type_data}' для пользователя с id_tg {user_id}: {e}")

                
    @staticmethod
    async def get_user_data(user_id: int, type_data: str) -> Union[User, str]:
        """
            Получение данных о пользователе:
            
                type_data: 'all' - Получение всех данных
                type_data: 'fio' - Получение ФИО
                type_data: 'phone_number' - Получение номера телефона
                type_data: 'encrypted_api_account_key' - Получение API ключа
                
        Args:
            user_id (int): User telegram ID
            type_data (str): Type of data requested

        Returns:
            User: Данные о пользователе
        """
        async for session in get_async_session():
            try:
                get_user_data_query = await session.execute(
                    select(User)
                    .where(User.id_tg == user_id)
                )
                user_data = get_user_data_query.scalar()
                match type_data:
                    case 'all':
                        return user_data
                    case _:
                        data_mapping = {
                            'fio': user_data.fio,
                            'phone_number': user_data.phone_number,
                            'encrypted_api_account_key': CIPHER_SUITE.decrypt(user_data.encrypted_api_account_key).decode('utf-8') 
                        }
                        
                        return data_mapping.get(type_data)
            except SQLAlchemyError as e:
                logging.error(f"Ошибка получения данных '{type_data}' для пользователя с id_tg {user_id}: {e}")
    