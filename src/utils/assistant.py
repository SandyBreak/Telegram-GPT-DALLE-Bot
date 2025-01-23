# -*- coding: UTF-8 -*-
from typing import Union

import requests

import logging

from services.postgres.user_service import UserService

class MinorOperations:
    def __init__(self):
        pass
    
    @staticmethod
    async def check_balance(user_id: int) -> Union[int, str]:
        """
        Вывод баланса пользователя
        """
        try:
            openai_api_key = await UserService.get_user_data(user_id, 'encrypted_api_account_key')

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            }
            logging.critical(openai_api_key)
            response = requests.post("https://api.proxyapi.ru/proxyapi/balance", headers=headers)

            if response.status_code == 200:
                return response.json()['balance']
            else:
                logging.error(f"Error: {response.status_code}, {response.text}")
        except Exception as e:
            logging.critical(f'Error checking balance! User ID: {user_id}')