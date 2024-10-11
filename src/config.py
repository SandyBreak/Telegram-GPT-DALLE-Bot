# -*- coding: UTF-8 -*-

import os

from cryptography.fernet import Fernet

LIST_USERS_TO_NEWSLETTER = []

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

CIPHER_SUITE = Fernet(os.environ.get('FERNET_KEY').encode('utf-8'))

POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
POSTGRES_DB = os.environ.get('POSTGRES_DB')

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{int(POSTGRES_PORT)}/{POSTGRES_DB}"