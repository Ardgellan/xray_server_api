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
        self._server_ip_and_port = f"{config.server_ip}:443" # Это используется только как дефолт, ссылка генерится ниже
        self._config_prefix = config.user_config_prefix

    async def _load_server_config(self) -> dict:
        async with aiofiles.open(self._config_path, "r") as f:
            return json.loads(await f.read())

    async def _save_server_config(self, config_data: dict):
        async with aiofiles.open(self._config_path, "w") as f:
            await f.write(json.dumps(config_data, indent=4))

    async def _restart_xray(self):
        os.system("systemctl restart xray")

    # --- ГЛАВНАЯ ЛОГИКА ДОБАВЛЕНИЯ ---
    async def add_new_user(self, config_name: str, user_telegram_id: int) -> tuple:
        credentials = CredentialsGenerator().generate_new_person(user_telegram_id=user_telegram_id)
        
        # 1. Настраиваем flow
        target_network = config.xray_network # "xhttp"
        
        if target_network in ["xhttp", "grpc"]:
            credentials["flow"] = ""
        else:
            credentials["flow"] = "xtls-rprx-vision" 

        # 2. Грузим конфиг
        server_config_json = await self._load_server_config()
        updated_config = deepcopy(server_config_json)

        # 3. ИЩЕМ НУЖНЫЙ INBOUND
        # Мы должны добавить юзера ТОЛЬКО в тот инбаунд, который соответствует XRAY_NETWORK
        user_added = False
        
        for inbound in updated_config["inbounds"]:
            stream = inbound.get("streamSettings", {})
            network = stream.get("network", "tcp") # дефолт tcp
            
            # Если нашли инбаунд с нужным протоколом (xhttp)
            if network == target_network:
                if "clients" not in inbound["settings"]:
                    inbound["settings"]["clients"] = []
                
                inbound["settings"]["clients"].append(credentials)
                user_added = True
                break # Добавили в целевой и выходим. В легаси (TCP) не добавляем.

        # Fallback: Если вдруг инбаунда с xhttp нет (скрипт миграции не сработал?), кидаем в первый
        if not user_added:
            logger.warning(f"Target network {target_network} not found in inbounds. Adding to first available.")
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

        # 5. Ссылка (порт 4433)
        link = await self.create_user_config_as_link_string(credentials["id"], config_name=config_name)
        return link, credentials["id"]

    async def create_user_config_as_link_string(self, uuid: str, config_name: str) -> str:
        # Используем порт из конфига (4433), а не зашитый
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
        # Собираем UUID со всех инбаундов
        conf = await self._load_server_config()
        uuids = []
        for inbound in conf.get("inbounds", []):
            clients = inbound.get("settings", {}).get("clients", [])
            for c in clients:
                uuids.append(c["id"])
        return list(set(uuids))

    async def disconnect_user_by_uuid(self, uuid: str) -> bool:
        # Удаляем отовсюду
        conf = await self._load_server_config()
        updated = deepcopy(conf)
        for inbound in updated["inbounds"]:
            if "clients" in inbound["settings"]:
                inbound["settings"]["clients"] = [
                    c for c in inbound["settings"]["clients"] if c["id"] != uuid
                ]
        return await self._apply_changes(updated, conf)

    async def disconnect_many_uuids(self, uuids: list[str]) -> bool:
        conf = await self._load_server_config()
        updated = deepcopy(conf)
        for inbound in updated["inbounds"]:
             if "clients" in inbound["settings"]:
                inbound["settings"]["clients"] = [
                    c for c in inbound["settings"]["clients"] if c["id"] not in uuids
                ]
        return await self._apply_changes(updated, conf)

    async def deactivate_user_configs_in_xray(self, uuids: list[str]) -> bool:
        return await self.disconnect_many_uuids(uuids)

    async def reactivate_user_configs_in_xray(self, config_uuids: list[str]) -> bool:
        if not config_uuids: return False

        server_config = await self._load_server_config()
        updated_config = deepcopy(server_config)

        target_net = config.xray_network
        current_flow = "" if target_net in ["xhttp", "grpc"] else "xtls-rprx-vision"

        # Ищем целевой инбаунд
        target_inbound = None
        for inbound in updated_config["inbounds"]:
            if inbound.get("streamSettings", {}).get("network", "tcp") == target_net:
                target_inbound = inbound
                break
        
        if not target_inbound:
            target_inbound = updated_config["inbounds"][0]

        for uuid in config_uuids:
            target_inbound["settings"]["clients"].append({
                "id": uuid,
                "email": f"{uuid}@example.com",
                "flow": current_flow
            })

        return await self._apply_changes(updated_config, server_config)

    async def get_active_client_count(self) -> int:
        try:
            return len(await self.get_all_uuids())
        except Exception as e:
            logger.error(e)
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