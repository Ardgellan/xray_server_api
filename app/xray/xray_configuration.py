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
        """Load server config from file"""
        async with aiofiles.open(self._config_path, "r") as f:
            config: dict = json.loads(await f.read())
        return config

    async def _save_server_config(self, config: dict):
        """Save server config to file"""
        async with aiofiles.open(self._config_path, "w") as f:
            dumped_json_config = json.dumps(config, indent=4)
            await f.write(dumped_json_config)

    async def _restart_xray(self):
        """Restart xray service"""
        os.system("systemctl restart xray")

    
    async def add_new_user(self, config_name: str, user_telegram_id: int) -> tuple:
        """Add new user to xray server config and return the config link and user UUID"""

        # Генерация новых учетных данных для пользователя
        credentials = CredentialsGenerator().generate_new_person(user_telegram_id=user_telegram_id)
    
        # --- ЛОГИКА XHTTP/GRPC ---
        # Если сеть xhttp или grpc, flow должен быть пустым!
        if config.xray_network in ["xhttp", "grpc"]:
            credentials["flow"] = ""
        # -------------------------

        # Загрузка текущей конфигурации сервера Xray
        server_config_json = await self._load_server_config()
        updated_config = deepcopy(server_config_json)

        # Добавление нового клиента в конфиг
        updated_config["inbounds"][0]["settings"]["clients"].append(credentials)

        # Сохраняем обновленный конфиг и перезапускаем сервер
        try:
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(e)
            await self._save_server_config(server_config_json)
            await self._restart_xray()
            raise Exception("Failed to update server config")

        # Генерируем ссылку на конфиг для нового пользователя
        link = await self.create_user_config_as_link_string(credentials["id"], config_name=config_name)

        # Возвращаем ссылку и UUID
        return link, credentials["id"]


    async def create_user_config_as_link_string(self, uuid: str, config_name: str) -> str:
        # Базовая часть ссылки
        link = (
            f"vless://{uuid}@{self._server_ip_and_port}"
            f"?security=reality"
            f"&sni={config.xray_sni}"
            f"&fp=chrome"
            f"&pbk={config.xray_publickey}"
            f"&sid={config.xray_shortid}"
            f"&encryption=none"
            f"&type={config.xray_network}" # Берем тип из .env (xhttp)
        )

        # Специфика параметров для разных протоколов
        if config.xray_network == "xhttp":
            link += f"&path={config.xray_path}"
            link += "&mode=auto"
        elif config.xray_network == "tcp":
            link += "&flow=xtls-rprx-vision"
        elif config.xray_network == "grpc":
            # Если вдруг вернешься на grpc, используем path как serviceName
            link += f"&serviceName={config.xray_path}"

        # Добавляем хештег (имя конфига)
        link += f"#{self._config_prefix}_{config_name}"
        
        return link

    async def get_all_uuids(self) -> list[str]:
        config = await self._load_server_config()
        uuids = [client["id"] for client in config["inbounds"][0]["settings"]["clients"]]
        return uuids

    async def disconnect_user_by_uuid(self, uuid: str) -> bool:
        config = await self._load_server_config()
        updated_config = deepcopy(config)
        updated_config["inbounds"][0]["settings"]["clients"] = [
            client
            for client in updated_config["inbounds"][0]["settings"]["clients"]
            if client["id"] != uuid
        ]
        return await self._apply_config_changes(updated_config, config)

    async def disconnect_many_uuids(self, uuids: list[str]) -> bool:
        config = await self._load_server_config()
        updated_config = deepcopy(config)
        updated_config["inbounds"][0]["settings"]["clients"] = [
            client
            for client in updated_config["inbounds"][0]["settings"]["clients"]
            if client["id"] not in uuids
        ]
        return await self._apply_config_changes(updated_config, config)

    async def deactivate_user_configs_in_xray(self, uuids: list[str]) -> bool:
        return await self.disconnect_many_uuids(uuids)

    async def reactivate_user_configs_in_xray(self, config_uuids: list[str]) -> bool:
        """
        Восстанавливаем конфиги в Xray для пользователей с переданными UUID.
        """
        if not config_uuids:
            logger.info("Нет конфигов для восстановления.")
            return False

        server_config = await self._load_server_config()
        updated_config = deepcopy(server_config)

        # Определяем flow на основе текущей сети
        current_flow = ""
        if config.xray_network == "tcp":
            current_flow = "xtls-rprx-vision"

        # Добавляем обратно конфиги по UUID
        for uuid in config_uuids:
            updated_config["inbounds"][0]["settings"]["clients"].append(
                {
                    "id": uuid,
                    "email": f"{uuid}@example.com",
                    "flow": current_flow, # Используем правильный flow
                }
            )

        return await self._apply_config_changes(updated_config, server_config)

    async def get_active_client_count(self) -> int:
        try:
            config = await self._load_server_config()
            clients = config.get("inbounds", [])[0].get("settings", {}).get("clients", [])
            return len(clients)
        except Exception as e:
            logger.error(f"Ошибка при подсчете активных клиентов: {e}")
            raise

    # Вспомогательный метод для сохранения и рестарта с откатом
    async def _apply_config_changes(self, new_config, old_config) -> bool:
        try:
            await self._save_server_config(new_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(e)
            await self._save_server_config(old_config)
            await self._restart_xray()
            return False
        else:
            return True