# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, LargeBinary, BOOLEAN, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base
from .temporary_dialog_data import TemporaryDialogData

class ModelRole(Base):
    __tablename__ = 'model_roles'
    
    id = Column(Integer, primary_key=True, nullable=False)
    
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="model_roles")
    
    name_role = Column(String(length=128), nullable=True)
    history_dialog = Column(JSON, default=[])
    
    temporary_dialog_name_role = relationship("TemporaryDialogData", back_populates="name_role")
