#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import asyncio
import logging

from aiogram import Bot, Dispatcher

from dotenv import load_dotenv

from aiogram.types.bot_command import BotCommand

from admin import admin_panel
from models.long_messages import SHORT_DESCRIPTION
from routers import actions, main_router, registration
from routers.commands import change_api_key, change_models, generate_dalle_img, role_options, simple_commands

from config import TELEGRAM_TOKEN


async def set_commands_and_description(bot: Bot) -> None:
    commands = [
        BotCommand(
            command="/cancel",
            description="Отмена текущего действия"
	    ),
        BotCommand(
            command="/balance",
            description="Узнать баланс аккаунта"
	    ),
        BotCommand(
            command="/view_set_options",
            description="Показать текущие настройки моделей"
	    ),
        BotCommand(
            command="/role_options",
            description="Управление ролями (только для текстовых моделей)"
	    ),
        BotCommand(
            command="/change_models",
            description="Выбрать модели для пользования"
        ),
        BotCommand(
            command="/img",
            description="Сгенерировать изображение"
	    ),
        BotCommand(
            command="/change_api_key",
            description="Поменять ключ аккаунта"
	    ),
        BotCommand(
            command="/tariffs",
            description="Узнать тарифы моделей"
	    ),
        BotCommand(
            command="/help",
            description="Помощь"
	    )
    ]
    #await bot.set_my_description(description=LONG_DESCRIPTION)
    await bot.set_my_short_description(short_description=SHORT_DESCRIPTION)
    await bot.set_my_commands(commands)
    
    
async def main():
    load_dotenv()#Потом убрать надо
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m %H:%M')
    
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    
    await set_commands_and_description(bot)
    
    dp.include_router(admin_panel.router)
    
    dp.include_router(actions.router)
    dp.include_router(main_router.router)
    dp.include_router(registration.router)
    
    #commands
    dp.include_router(change_api_key.router)
    dp.include_router(change_models.router)
    dp.include_router(generate_dalle_img.router)
    dp.include_router(role_options.router)
    dp.include_router(simple_commands.router)
    

    await dp.start_polling(bot)
    logging.warning('BOT STARTED')
    

if __name__ == '__main__':
    asyncio.run(main())
    