# -*- coding: UTF-8 -*-

from typing import Optional
import logging

from sqlalchemy import delete, select, update

from services.postgres.database import get_async_session

from models.table_models.admin_group import AdminGroup
from models.table_models.user import User


class GroupService:
    def __init__(self):
        pass


    @staticmethod
    async def group_init(id_group: int) -> None:
        """
            Идентификация группы в которую добавлен бот и сохранение ее ID
        
        Args:
            id_group (int): Telegram Group ID
        """
        try:
            async for session in get_async_session():
                session.add(AdminGroup(group_id=id_group))
                await session.commit()
        except Exception as e:
            logging.error(f"Ошибка идентификации группы: {e}")
    
    
    @staticmethod
    async def group_reset() -> None:
        """
        Удаление ID группы при удалении бота из групыы
        """
        try:
            async for session in get_async_session():
                await session.execute(
                    delete(AdminGroup)
                )
                await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(f"Ошибка сброса группы: {e}")
    
    
    @staticmethod
    async def get_group_id() -> Optional[str]:
        """
        Получение ID группы
        """
        try:
            async for session in get_async_session():
                get_group_id = await session.execute(
                    select(AdminGroup.group_id)
                )
                
                return get_group_id.scalar()
        except Exception as e:
            logging.error(f"Ошибка получения ID группы: {e}")
            
            
    @staticmethod
    async def get_user_message_thread_id(user_id: int) -> Optional[int]:
        """
        Получение id чата с пользователем в группе
        """
        try:
            async for session in get_async_session():
                get_user_id_topic_chat = await session.execute(
                    select(User.id_topic_chat)
                    .select_from(User)
                    .where(User.id_tg == user_id)
                )
                return get_user_id_topic_chat.scalar()
        except Exception as e:
            logging.error(f"Ошибка получения id чата в группе для пользователя с id_tg {user_id}: {e}")

    
    @staticmethod
    async def save_user_message_thread_id(user_id: int, id_topic_chat: int) -> None:
        """
        Сохрранение id чата с пользователем в группе
        """
        try:
            async for session in get_async_session():
                await session.execute(
                    update(User)
                    .where(User.id_tg==user_id)
                    .values(
                        id_topic_chat=id_topic_chat
                    )
                )
                await session.commit()
        except Exception as e:
            logging.error(f"Ошибка сохранения id чата в группе для пользователя с id_tg {user_id}: {e}")
            
    
    @staticmethod
    async def get_user_id(id_topic_chat: int) -> Optional[int]:
        """
        Получение user_id пользователя у которого id чата в группе равно id_topic_chat
        """
        try:
            async for session in get_async_session():
                get_user_id_query = await session.execute(
                    select(User.id_tg)
                    .select_from(User)
                    .where(User.id_topic_chat == id_topic_chat)
                )
                return get_user_id_query.scalar()
        except Exception as e:
            logging.error(f"Ошибка при получении id пользователя по id чата группы: {e}")
    