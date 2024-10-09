# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, BigInteger
from .base import Base


class AdminGroup(Base):
    __tablename__ = 'admin_group'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, nullable=False)
