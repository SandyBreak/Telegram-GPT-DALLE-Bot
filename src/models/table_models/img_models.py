# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .temporary_dialog_data import TemporaryDialogData

class ImgModel(Base):
    __tablename__ = 'img_models'
    
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=32), nullable=False)
    value = Column(String(length=32), nullable=False)
    
    img_models = relationship("TemporaryDialogData", back_populates="img_model")

