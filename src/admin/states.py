# -*- coding: UTF-8 -*-

from aiogram.fsm.state import State, StatesGroup
     
    
class AdminPanelStates(StatesGroup):
    
    base_state = State()
    
    launch_newsletter = State()