from os import getenv
from dotenv import load_dotenv
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
        
        # --- НОВЫЕ ПЕРЕМЕННЫЕ ---
        self._xray_network: str = self._get_xray_network()
        self._xray_path: str = self._get_xray_path()
        self._xray_link_port: str = self._get_xray_link_port()

    def _get_user_config_prefix(self) -> str:
        return getenv("USER_CONFIGS_PREFIX", "VPNizator")

    def _get_xray_config_path(self) -> str:
        return getenv("XRAY_CONFIG_PATH", "/usr/local/etc/xray/config.json")

    def _get_server_ip(self) -> str:
        return IPInfo().get_server_ip()

    def _get_server_country(self) -> str:
        return getenv("SERVER_COUNTRY", "Unknown")

    def _get_server_country_code(self) -> str:
        return getenv("SERVER_COUNTRY_CODE", "UN")

    def _get_xray_sni(self) -> str:
        return getenv("XRAY_SNI", "www.microsoft.com")

    def _get_xray_privatekey(self) -> str:
        val = getenv("XRAY_PRIVATEKEY")
        if not val: raise DotEnvVariableNotFound("XRAY_PRIVATEKEY")
        return val

    def _get_xray_publickey(self) -> str:
        val = getenv("XRAY_PUBLICKEY")
        if not val: raise DotEnvVariableNotFound("XRAY_PUBLICKEY")
        return val

    def _get_xray_shortid(self) -> str:
        val = getenv("XRAY_SHORTID")
        if not val: raise DotEnvVariableNotFound("XRAY_SHORTID")
        return val

    def _get_domain_name(self) -> str:
        return getenv("XRAY_DOMAIN_NAME", "vpnizator.online")

    # --- НОВЫЕ МЕТОДЫ ---
    def _get_xray_network(self) -> str:
        return getenv("XRAY_NETWORK", "xhttp")

    def _get_xray_path(self) -> str:
        return getenv("XRAY_PATH", "/update")

    def _get_xray_link_port(self) -> str:
        # По умолчанию 443, но скрипт миграции задаст 4433
        return getenv("XRAY_LINK_PORT", "443")

    @property
    def user_config_prefix(self) -> str: return self._user_config_prefix
    @property
    def xray_config_path(self) -> str: return self._xray_config_path
    @property
    def server_ip(self) -> str: return self._server_ip
    @property
    def xray_sni(self) -> str: return self._xray_sni
    @property
    def xray_privatekey(self) -> str: return self._xray_privatekey
    @property
    def xray_publickey(self) -> str: return self._xray_publickey
    @property
    def xray_shortid(self) -> str: return self._xray_shortid
    @property
    def domain_name(self) -> str: return self._domain_name
    @property
    def server_country(self) -> str: return self._server_country
    @property
    def server_country_code(self) -> str: return self._server_country_code
    
    @property
    def xray_network(self) -> str: return self._xray_network
    @property
    def xray_path(self) -> str: return self._xray_path
    @property
    def xray_link_port(self) -> str: return self._xray_link_port