# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, LargeBinary, BOOLEAN
from sqlalchemy.orm import relationship

from .base import Base
from .model_roles import ModelRole

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, nullable=False)
    
    id_tg = Column(BigInteger, nullable=True)
    nickname = Column(String(length=64), nullable=True)
    fullname = Column(String(length=64), nullable=True)
    
    fio = Column(String(length=256), nullable=True)
    phone_number = Column(String(length=320), nullable=True)
    encrypted_api_account_key = Column(LargeBinary, nullable=True)
    
    date_reg = Column(DateTime, nullable=True)
    id_topic_chat = Column(BigInteger, nullable=True)
    
    access_flag = Column(BOOLEAN, nullable=True)

    model_roles = relationship("ModelRole", back_populates="owner")