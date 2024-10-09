# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .model_roles import ModelRole

class LlmModel(Base):
    __tablename__ = 'llm_models'
    
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=32), nullable=False)
    value = Column(String(length=32), nullable=False)
    
    llm_models = relationship("TemporaryDialogData", back_populates="llm_model")

