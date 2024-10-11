# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, LargeBinary, BOOLEAN, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class TemporaryDialogData(Base):
    __tablename__ = 'temporary_dialog_data'
    
    id = Column(Integer, primary_key=True, nullable=False)
    
    id_tg = Column(BigInteger, nullable=False)
    
    role_id = Column(Integer, ForeignKey('model_roles.id'), nullable=True)
    name_role = relationship("ModelRole", foreign_keys=[role_id], back_populates="temporary_dialog_name_role") 
    
    img_model_id = Column(Integer, ForeignKey('img_models.id'), nullable=True)
    img_model = relationship("ImgModel", back_populates="img_models")
    
    llm_model_id = Column(Integer, ForeignKey('llm_models.id'), nullable=True)
    llm_model = relationship("LlmModel", back_populates="llm_models")
    
    quality_generated_image = Column(String(length=16), nullable=True)
    
