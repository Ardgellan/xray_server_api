from os import getenv

from dotenv import load_dotenv, set_key
from flag import flag

from app.utils.ip_info import IPInfo


class DotEnvVariableNotFound(Exception):
    def __init__(self, variable_name: str):
        self.variable_name = variable_name

    def __str__(self):
        return f"Variable {self.variable_name} not found in .env file"


class Configuration:
    def __init__(self):
        load_dotenv()
        self._user_config_prefix: str = self._get_user_config_prefix()
        self._xray_config_path: str = self._get_xray_config_path()
        self._server_ip: str = self._get_server_ip()
        self._server_country: str = self._get_server_country()
        self._server_country_code: str = self._get_server_country_code()
        self._xray_sni: str = self._get_xray_sni()
        self._xray_privatekey: str = self._get_xray_privatekey()
        self._xray_publickey: str = self._get_xray_publickey()
        self._xray_shortid: str = self._get_xray_shortid()
        self._domain_name: str = self._get_domain_name()
        self._save_country_in_env(self._server_country, self._server_country_code)

    def _get_user_config_prefix(self) -> str:
        user_config_prefix = getenv("USER_CONFIGS_PREFIX")
        if not user_config_prefix:
            raise DotEnvVariableNotFound("USER_CONFIGS_PREFIX")
        return user_config_prefix

    def _get_xray_config_path(self) -> str:
        xray_config_path = getenv("XRAY_CONFIG_PATH")
        if not xray_config_path:
            raise DotEnvVariableNotFound("XRAY_CONFIG_PATH")
        return xray_config_path

    def _get_server_ip(self) -> str:
        return IPInfo().get_server_ip()

    # def _get_server_country(self) -> str:
    #     ip_info = IPInfo()
    #     server_country = ip_info.get_server_country_name()
    #     server_country_code = ip_info.get_server_country_code()
    #     return f"{flag(server_country_code)} {server_country}"

    def _get_server_country(self) -> str:
        """Возвращает название страны, в которой находится сервер"""
        ip_info = IPInfo()
        return ip_info.get_server_country_name()

    def _get_server_country_code(self) -> str:
        """Возвращает код страны, в которой находится сервер"""
        ip_info = IPInfo()
        return ip_info.get_server_country_code()

    def _get_xray_sni(self) -> str:
        xray_sni = getenv("XRAY_SNI")
        if not xray_sni:
            raise DotEnvVariableNotFound("XRAY_SNI")
        return xray_sni

    def _get_xray_privatekey(self) -> str:
        xray_privatekey = getenv("XRAY_PRIVATEKEY")
        if not xray_privatekey:
            raise DotEnvVariableNotFound("XRAY_PRIVATEKEY")
        return xray_privatekey

    def _get_xray_publickey(self) -> str:
        xray_publickey = getenv("XRAY_PUBLICKEY")
        if not xray_publickey:
            raise DotEnvVariableNotFound("XRAY_PUBLICKEY")
        return xray_publickey

    def _get_xray_shortid(self) -> str:
        xray_shortid = getenv("XRAY_SHORTID")
        if not xray_shortid:
            raise DotEnvVariableNotFound("XRAY_SHORTID")
        return xray_shortid

    def _get_domain_name(self) -> str:
        domain_name = getenv("XRAY_DOMAIN_NAME")
        if not domain_name:
            raise DotEnvVariableNotFound("XRAY_DOMAIN_NAME")
        return domain_name

    def _save_country_in_env(self, country: str, country_code: str):
        """Если в .env нет переменных для страны и её кода, то добавляем их."""
        if not os.getenv("SERVER_COUNTRY"):
            set_key(".env", "SERVER_COUNTRY", country)
        
        if not os.getenv("SERVER_COUNTRY_CODE"):
            set_key(".env", "SERVER_COUNTRY_CODE", country_code)


    @property
    def user_config_prefix(self) -> str:
        return self._user_config_prefix

    @property
    def xray_config_path(self) -> str:
        return self._xray_config_path

    @property
    def server_ip(self) -> str:
        return self._server_ip

    @property
    def xray_sni(self) -> str:
        return self._xray_sni

    @property
    def xray_privatekey(self) -> str:
        return self._xray_privatekey

    @property
    def xray_publickey(self) -> str:
        return self._xray_publickey

    @property
    def xray_shortid(self) -> str:
        return self._xray_shortid

    @property
    def domain_name(self) -> str:
        return self._domain_name

    @property
    def server_country(self) -> str:
        return f"{self._server_country} ({self._server_country_code})"