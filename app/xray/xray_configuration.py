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
            return json.loads(await f.read())

    async def _save_server_config(self, config_data: dict):
        """Save server config to file"""
        async with aiofiles.open(self._config_path, "w") as f:
            await f.write(json.dumps(config_data, indent=4))

    async def _restart_xray(self):
        """Restart xray service"""
        os.system("systemctl restart xray")

    # --- ГЛАВНАЯ ЛОГИКА ДОБАВЛЕНИЯ ---
    async def add_new_user(self, config_name: str, user_telegram_id: int) -> tuple:
        credentials = CredentialsGenerator().generate_new_person(user_telegram_id=user_telegram_id)
        
        # 1. Настраиваем flow
        target_network = config.xray_network
        
        if target_network in ["xhttp", "grpc"]:
            credentials["flow"] = ""
        else:
            credentials["flow"] = "xtls-rprx-vision" 

        # 2. Грузим конфиг
        server_config_json = await self._load_server_config()
        updated_config = deepcopy(server_config_json)

        # 3. ИЩЕМ НУЖНЫЙ INBOUND
        user_added = False
        
        for inbound in updated_config.get("inbounds", []):
            stream = inbound.get("streamSettings", {})
            network = stream.get("network", "tcp")
            
            if network == target_network:
                if "settings" not in inbound:
                    inbound["settings"] = {}
                if "clients" not in inbound["settings"]:
                    inbound["settings"]["clients"] = []
                
                inbound["settings"]["clients"].append(credentials)
                user_added = True
                break

        # Fallback
        if not user_added:
            logger.warning(f"Target network {target_network} not found. Adding to first inbound.")
            # Безопасное добавление в первый инбаунд
            if updated_config["inbounds"]:
                if "settings" not in updated_config["inbounds"][0]:
                    updated_config["inbounds"][0]["settings"] = {}
                if "clients" not in updated_config["inbounds"][0]["settings"]:
                    updated_config["inbounds"][0]["settings"]["clients"] = []
                updated_config["inbounds"][0]["settings"]["clients"].append(credentials)

        # 4. Сохраняем
        try:
            await self._save_server_config(updated_config)
            await self._restart_xray()
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            await self._save_server_config(server_config_json)
            await self._restart_xray()
            raise Exception("Failed to update server config")

        # 5. Ссылка
        link = await self.create_user_config_as_link_string(credentials["id"], config_name=config_name)
        return link, credentials["id"]

    async def create_user_config_as_link_string(self, uuid: str, config_name: str) -> str:
        target_port = config.xray_link_port
        
        link = (
            f"vless://{uuid}@{config.server_ip}:{target_port}"
            f"?security=reality"
            f"&sni={config.xray_sni}"
            f"&fp=chrome"
            f"&pbk={config.xray_publickey}"
            f"&sid={config.xray_shortid}"
            f"&encryption=none"
            f"&type={config.xray_network}" 
        )
        
        if config.xray_network == "xhttp":
            link += f"&path={config.xray_path}&mode=auto"
        elif config.xray_network == "tcp":
            link += "&flow=xtls-rprx-vision"
        elif config.xray_network == "grpc":
            link += f"&serviceName={config.xray_path}"
            
        link += f"#{self._config_prefix}_{config_name}"
        return link

    async def get_all_uuids(self) -> list[str]:
        conf = await self._load_server_config()
        uuids = []
        for inbound in conf.get("inbounds", []):
            clients = inbound.get("settings", {}).get("clients", [])
            for c in clients:
                uuids.append(c["id"])
        return list(set(uuids))

    # --- БЕЗОПАСНОЕ УДАЛЕНИЕ ---
    async def disconnect_user_by_uuid(self, uuid: str) -> bool:
        conf = await self._load_server_config()
        updated = deepcopy(conf)
        
        modified = False
        for inbound in updated.get("inbounds", []):
            # Безопасное получение settings, чтобы не словить KeyError
            settings = inbound.get("settings", {})
            if "clients" in settings:
                original_len = len(settings["clients"])
                settings["clients"] = [
                    c for c in settings["clients"] if c.get("id") != uuid
                ]
                # Если длина изменилась, значит кого-то удалили
                if len(settings["clients"]) < original_len:
                    modified = True
                    # Важно: обновляем словарь в инбаунде (хотя он и так по ссылке, но для надежности)
                    inbound["settings"] = settings

        if modified:
            return await self._apply_changes(updated, conf)
        else:
            logger.info(f"User {uuid} not found, skipping restart.")
            return True # Юзера и так нет, считаем что успех

    async def disconnect_many_uuids(self, uuids: list[str]) -> bool:
        conf = await self._load_server_config()
        updated = deepcopy(conf)
        
        modified = False
        for inbound in updated.get("inbounds", []):
            settings = inbound.get("settings", {})
            if "clients" in settings:
                original_len = len(settings["clients"])
                settings["clients"] = [
                    c for c in settings["clients"] if c.get("id") not in uuids
                ]
                if len(settings["clients"]) < original_len:
                    modified = True
                    inbound["settings"] = settings

        if modified:
            return await self._apply_changes(updated, conf)
        else:
            return True

    async def deactivate_user_configs_in_xray(self, uuids: list[str]) -> bool:
        return await self.disconnect_many_uuids(uuids)

    async def reactivate_user_configs_in_xray(self, config_uuids: list[str]) -> bool:
        if not config_uuids: return False

        server_config = await self._load_server_config()
        updated_config = deepcopy(server_config)

        target_net = config.xray_network
        current_flow = "" if target_net in ["xhttp", "grpc"] else "xtls-rprx-vision"

        target_inbound = None
        for inbound in updated_config.get("inbounds", []):
            if inbound.get("streamSettings", {}).get("network", "tcp") == target_net:
                target_inbound = inbound
                break
        
        if not target_inbound and updated_config.get("inbounds"):
            target_inbound = updated_config["inbounds"][0]

        if target_inbound:
            if "settings" not in target_inbound: target_inbound["settings"] = {}
            if "clients" not in target_inbound["settings"]: target_inbound["settings"]["clients"] = []

            for uuid in config_uuids:
                existing_ids = [c["id"] for c in target_inbound["settings"]["clients"]]
                if uuid not in existing_ids:
                    target_inbound["settings"]["clients"].append({
                        "id": uuid,
                        "email": f"{uuid}@example.com",
                        "flow": current_flow
                    })

        return await self._apply_changes(updated_config, server_config)

    async def get_active_client_count(self) -> int:
        try:
            server_config = await self._load_server_config()
            target_net = config.xray_network
            
            for inbound in server_config.get("inbounds", []):
                network = inbound.get("streamSettings", {}).get("network", "tcp")
                if network == target_net:
                    clients = inbound.get("settings", {}).get("clients", [])
                    return len(clients)
            return 0
        except Exception as e:
            logger.error(f"Stat error: {e}")
            return 0
            
    async def _apply_changes(self, new_conf, old_conf) -> bool:
        try:
            await self._save_server_config(new_conf)
            await self._restart_xray()
            return True
        except Exception as e:
            logger.error(e)
            await self._save_server_config(old_conf)
            await self._restart_xray()
            return False