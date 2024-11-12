import asyncio

import json
import os
from copy import deepcopy

import aiofiles
from loguru import logger

from app.data import config

from .credentials_generator import CredentialsGenerator


class XrayConfiguration:
    def __init__(self):
        self._config_path = config.xray_config_path
        self._server_ip_and_port = f"{config.server_ip}:443"
        self._config_prefix = config.user_config_prefix

    async def _load_server_config(self) -> dict:
        """Load server config from file

        Returns:
            dict: server config in dict format (json)
        """
        async with aiofiles.open(self._config_path, "r") as f:
            config: dict = json.loads(await f.read())
        return config

    async def _save_server_config(self, config: dict):
        """Save server config to file

        Args:
            config (dict): server config in dict format (json)
        """
        async with aiofiles.open(self._config_path, "w") as f:
            dumped_json_config = json.dumps(config, indent=4)
            await f.write(dumped_json_config)

    async def _restart_xray(self):
        """Restart xray service"""
        os.system("systemctl restart xray")

    # async def add_new_user(self, config_name: str, user_telegram_id: int) -> str:
    #     """Add new user to xray server config

    #     Returns:
    #         str: user config as link string
    #     """
    #     credentials = CredentialsGenerator().generate_new_person(user_telegram_id=user_telegram_id)
    #     config = await self._load_server_config()
    #     updated_config = deepcopy(config)
    #     updated_config["inbounds"][0]["settings"]["clients"].append(credentials)
    #     # try:
    #         await self._save_server_config(updated_config)
    #         await self._restart_xray()
    #     # except Exception as e:
    #         logger.error(e)
    #         await self._save_server_config(config)
    #         await self._restart_xray()
    #     else:
    #         # Добавляем транзакцию и механизм повторных попыток для вставки в базу данных
    #         attempts = 3  # Количество попыток
    #         success = False
    #         for attempt in range(attempts):
    #             try:
    #                 # Открываем транзакцию и пытаемся добавить новый конфиг
    #                 async with db_manager.transaction() as conn:
    #                     await db_manager.insert_new_vpn_config(
    #                         user_id=user_telegram_id,
    #                         config_name=config_name,
    #                         config_uuid=credentials["id"],
    #                         conn=conn,  # Передаем транзакцию для консистентности
    #                     )
    #                 success = True
    #                 break  # Если вставка успешна, выходим из цикла
    #             except Exception as e:
    #                 logger.error(
    #                     f"Ошибка при добавлении конфигурации VPN для пользователя {user_telegram_id} (попытка {attempt + 1}): {str(e)}"
    #                 )
    #                 await asyncio.sleep(2)  # Задержка перед повторной попыткой

    #         if success:
    #             # Возвращаем ссылку на конфиг после успешной вставки
    #             return await self.create_user_config_as_link_string(
    #                 credentials["id"], config_name=config_name
    #             )
    #         else:
    #             # Если все попытки не удались, логируем ошибку
    #             logger.critical(
    #                 f"Не удалось добавить конфигурацию для пользователя {user_telegram_id} после {attempts} попыток."
    #             )

    #             # Отправляем сообщение пользователю на русском и английском языках
    #             error_message = (
    #                 "⚠️ Упс, похоже возникла ошибка при генерации VPN-конфига. Попробуйте еще раз, в меню 'Мои VPN соединения!'\n\n"
    #                 "⚠️ Oops, it looks like there was an error generating the VPN config. Please try again in the 'My VPN Connections' menu!"
    #             )

    #             await dp.bot.send_message(
    #                 chat_id=user_telegram_id,
    #                 text=error_message,
    #             )

    #             raise Exception(
    #                 "Не удалось добавить конфигурацию VPN в базу данных. Пожалуйста, проверьте вручную."
    #             )

    
    async def add_new_user(self, config_name: str, user_telegram_id: int) -> tuple:
        """Add new user to xray server config and return the config link and user UUID"""

        # Генерация новых учетных данных для пользователя
        credentials = CredentialsGenerator().generate_new_person(user_telegram_id=user_telegram_id)
    
        # Загрузка текущей конфигурации сервера Xray
        config = await self._load_server_config()
        updated_config = deepcopy(config)

        # Добавление нового клиента в конфиг
        updated_config["inbounds"][0]["settings"]["clients"].append(credentials)

        # Сохраняем обновленный конфиг и перезапускаем сервер
        try:
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(e)
            await self._save_server_config(config)
            await self._restart_xray()
            raise Exception("Failed to update server config")

        # Генерируем ссылку на конфиг для нового пользователя
        link = await self.create_user_config_as_link_string(credentials["id"], config_name=config_name)

        # Возвращаем ссылку и UUID
        return link, credentials["id"]  # Ссылка и UUID пользователя


    async def create_user_config_as_link_string(self, uuid: str, config_name: str) -> str:
        link = (
            f"vless://{uuid}@{self._server_ip_and_port}"
            f"?security=reality"
            f"&sni={config.xray_sni}"
            "&fp=chrome"
            f"&pbk={config.xray_publickey}"
            f"&sid={config.xray_shortid}"
            "&type=tcp"
            "&flow=xtls-rprx-vision"
            "&encryption=none"
            "#"
            f"{self._config_prefix}_{config_name}"
        )
        return link

    async def get_all_uuids(self) -> list[str]:
        config = await self._load_server_config()
        uuids = [client["id"] for client in config["inbounds"][0]["settings"]["clients"]]
        return uuids

    async def disconnect_user_by_uuid(self, uuid: str) -> bool:
        """Disconnect user by uuid

        Args:
            uuid (str): user uuid in xray config

        Returns:
            bool: True if user was disconnected, False if not
        """
        config = await self._load_server_config()
        updated_config = deepcopy(config)
        updated_config["inbounds"][0]["settings"]["clients"] = [
            client
            for client in updated_config["inbounds"][0]["settings"]["clients"]
            if client["id"] != uuid
        ]
        try:
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(e)
            await self._save_server_config(config)
            await self._restart_xray()
            return False
        else:
            return True

    async def disconnect_many_uuids(self, uuids: list[str]) -> bool:
        """Deletes many configs by uuids

        Args:
            uuids (list[str]): list of users uuids in xray config

        Returns:
            bool: True if users was disconnected, False if not
        """
        config = await self._load_server_config()
        updated_config = deepcopy(config)
        updated_config["inbounds"][0]["settings"]["clients"] = [
            client
            for client in updated_config["inbounds"][0]["settings"]["clients"]
            if client["id"] not in uuids
        ]
        try:
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(e)
            await self._save_server_config(config)
            await self._restart_xray()
            return False
        else:
            await db_manager.delete_many_vpn_configs_by_uuids(uuids=uuids)
            return True

    # async def disconnect_user_by_telegram_id(self, telegram_id: int) -> bool:
    #     """Disconnect user by telegram id

    #     Args:
    #         telegram_id (int): user telegram id

    #     Returns:
    #         bool: True if user was disconnected, False if not
    #     """
    #     user_configs_uuids = await db_manager.get_user_config_names_and_uuids(user_id=telegram_id)
    #     if user_configs_uuids:
    #         uuids = [config.config_uuid for config in user_configs_uuids]
    #         return await self.disconnect_many_uuids(uuids=uuids)
    #     else:
    #         return False

    async def deactivate_user_configs_in_xray(self, uuids: list[str]) -> bool:
        """Временно деактивируем конфиги в конфигурации Xray"""
        config = await self._load_server_config()
        updated_config = deepcopy(config)

        # Убираем конфиги пользователей, но сохраняем их где-то
        updated_config["inbounds"][0]["settings"]["clients"] = [
            client
            for client in updated_config["inbounds"][0]["settings"]["clients"]
            if client["id"] not in uuids
        ]

        try:
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(e)
            await self._save_server_config(config)
            await self._restart_xray()
            return False

        return True

    # async def reactivate_user_configs_in_xray(self, user_ids: list[int]) -> bool:
    #     """Восстанавливаем конфиги в Xray для всех пользователей с продленной подпиской"""

    #     # Собираем все UUID конфигов пользователей
    #     all_configs_to_restore = []

    #     for user_id in user_ids:
    #         await db_manager.update_subscription_status(user_id=user_id, is_active=True)
    #         # Получаем только UUID всех конфигов пользователя
    #         user_uuids = await db_manager.get_user_uuids_by_user_id(user_id=user_id)
    #         if user_uuids:
    #             all_configs_to_restore.extend(user_uuids)

    #     # Проверяем, если нет конфигов для восстановления
    #     if not all_configs_to_restore:
    #         # logger.info("Нет конфигов для восстановления.")
    #         return False

    #     # Загружаем текущий конфиг сервера
    #     server_config = await self._load_server_config()
    #     updated_config = deepcopy(server_config)

    #     # Добавляем обратно конфиги по UUID
    #     for uuid in all_configs_to_restore:
    #         updated_config["inbounds"][0]["settings"]["clients"].append(
    #             {
    #                 "id": uuid,
    #                 "email": f"{uuid}@example.com",  # Здесь можно использовать email-шаблон
    #                 "flow": "xtls-rprx-vision",  # Xray flow
    #             }
    #         )

    #     try:
    #         # Сохраняем обновленный конфиг и перезагружаем Xray
    #         await self._save_server_config(updated_config)
    #         await self._restart_xray()
    #     except Exception as e:
    #         logger.error(f"Ошибка при восстановлении конфигов: {e}")
    #         return False

    #     # logger.info(f"Все конфиги для пользователей {user_ids} успешно восстановлены.")
    #     return True

    async def reactivate_user_configs_in_xray(self, config_uuids: list[str]) -> bool:
        """
        Восстанавливаем конфиги в Xray для пользователей с переданными UUID.
        Возвращает True, если восстановление прошло успешно.
        """

        # Проверяем, если нет конфигов для восстановления
        if not config_uuids:
            logger.info("Нет конфигов для восстановления.")
            return False

        # Загружаем текущий конфиг сервера
        server_config = await self._load_server_config()
        updated_config = deepcopy(server_config)

        # Добавляем обратно конфиги по UUID
        for uuid in config_uuids:
            updated_config["inbounds"][0]["settings"]["clients"].append(
                {
                    "id": uuid,
                    "email": f"{uuid}@example.com",  # Здесь можно использовать email-шаблон
                    "flow": "xtls-rprx-vision",  # Xray flow
                }
            )

        try:
            # Сохраняем обновленный конфиг и перезагружаем Xray
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(f"Ошибка при восстановлении конфигов: {e}")
            return False

        # logger.info(f"Все конфиги успешно восстановлены для UUIDs: {', '.join(config_uuids)}.")
        return True
