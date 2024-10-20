# -*- coding: UTF-8 -*-
import logging
import requests

from services.postgres.user_service import UserService

class MinorOperations:
    def __init__(self):
        pass
    
    @staticmethod
    async def check_balance(user_id: int) -> None:
        """
        Вывод баланса пользователя
        """
        try:
            openai_api_key = await UserService.get_user_data(user_id, 'encrypted_api_account_key')

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            }

            response = requests.post("https://api.proxyapi.ru/proxyapi/balance", headers=headers)

            if response.status_code == 200:
                return response.json()['balance']
            else:
                logging.error("Error:", response.status_code, response.text)
        except Exception as e:
            logging.critical(f'Error checking balance! User ID: {user_id}')