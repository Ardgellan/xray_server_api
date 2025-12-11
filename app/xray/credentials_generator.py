import os


class CredentialsGenerator:
    def __init__(self) -> None:
        self._xray_executable_path = "/usr/local/bin/xray"

    def generate_uuid(self) -> str:
        return os.popen(f"{self._xray_executable_path} uuid").read().strip()

    def generate_new_person(self, user_telegram_id: int, custom_uuid: str) -> dict[str, str]:
            # 💡 ИСПОЛЬЗОВАНИЕ UUID: Если custom_uuid предоставлен, используем его; иначе генерируем.
            if custom_uuid:
                uuid = custom_uuid
            else:
                uuid = self.generate_uuid()
                
            return {
                "id": uuid,
                "email": f"{uuid}@example.com",
                "flow": "xtls-rprx-vision",
            }
