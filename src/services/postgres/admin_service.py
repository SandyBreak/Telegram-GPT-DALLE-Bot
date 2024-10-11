# -*- coding: UTF-8 -*-

from typing import Union
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from services.postgres.database import get_async_session

from models.table_models.model_roles import ModelRole
from models.table_models.llm_models import LlmModel
from models.table_models.img_models import ImgModel
from models.table_models.user import User

class AdminService:
    def __init__(self):
        pass
        
    
    @staticmethod
    async def get_table(table_name:str) -> Union[User]:
        """
        Получение данных из таблицы
        """
        async for session in get_async_session():
            try:
                match table_name:
                    case 'user':
                        result = await session.execute(select(User))
                    case 'llm_models':
                        result = await session.execute(select(LlmModel))
                    case 'img_models':
                        result = await session.execute(select(ImgModel))
                    case 'model_roles':
                        result = await session.execute(select(ModelRole))
                return_data = result.scalars().all()
                return return_data
                    
            except SQLAlchemyError as e:
                logging.error(f"Ошибка при получении данных из таблицы {table_name}: {e}")
                raise e
        
        
        
        