#!/bin/bash

# Функция для вывода красного предупреждения
function red_alert() {
    echo -e "\033[31mВНИМАНИЕ! Этот скрипт: $1\033[0m"
    read -p "Вы уверены, что хотите продолжить? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        echo "Процесс отменен."
        exit 1
    fi

    echo -e "\033[31mВЫ ТОЧНО УВЕРЕНЫ?!\033[0m"
    read -p "Введите yes для продолжения: " confirm2
    if [[ "$confirm2" != "yes" ]]; then
        echo "Процесс отменен."
        exit 1
    fi
}

# Используем предупреждение для начала
red_alert "ПЕРЕУСТАНАВЛИВАЕТ XRAY_API ЗАНОВО, В ТОМ ЧИСЛЕ УДАЛЯЯ ВСЕ ПРЕДЫДУЩИЕ ДАННЫЕ!"

Red='\033[0;31m'
Green='\033[0;32m'
Blue='\033[0;34m'
Yellow='\033[1;33m'
White='\033[1;37m'
Default='\033[0m'

current_os_user=$(whoami)

# sudo vim /etc/sysctl.conf

# Удаляем все старые данные
rm -rf ~/autoinstall_xray_api.sh
rm -rf ~/get-pip.py
rm -rf ~/xray_server_api
sudo systemctl stop xray_api.service
rm -rf /etc/systemd/system/xray_api.service
rm -f ~/nohup.out

rm -rf /usr/local/etc #json.config is also included
rm -rf /usr/local/bin
sudo systemctl stop xray.service
rm -rf /etc/systemd/system/xray.service
rm -rf /etc/systemd/system/xray.service.d
rm -rf /etc/systemd/system/xray@.service
rm -rf /etc/systemd/system/xray@.service.d
rm -rf /usr/local/lib

sudo systemctl daemon-reload

# # Расширение системы, если она была минимизирована
yes | unminimize

# Апдейт и апгрейд системы
echo "Обновляем систему..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python 3.11 и необходимые пакеты
echo "Устанавливаем Python 3.11 и пакеты разработки..."
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-distutils python3.11-venv

# Устанавливаем pip для Python 3
echo "Устанавливаем pip..."
sudo curl https://bootstrap.pypa.io/get-pip.py -o /root/get-pip.py
python3.11 /root/get-pip.py

# Устанавливаем Poetry для управления зависимостями
echo "Устанавливаем Poetry..."
pip3.11 install poetry

# Устанавливаем Git, если он еще не установлен
echo "Устанавливаем Git..."
sudo apt install git -y

# Установка часового пояса на Москву
echo "Настраиваем часовой пояс на Москву..."
sudo timedatectl set-timezone Europe/Moscow

# Клонирование репозитория и установка зависимостей
echo "Клонируем репозиторий vpnizator-xray-api и устанавливаем зависимости..."
git clone https://github.com/Ardgellan/xray_server_api.git
cd xray_server_api  # Убедитесь, что папка совпадает с названием репозитория

# Устанавливаем зависимости через Poetry
echo "Устанавливаем зависимости проекта через Poetry..."
poetry install --no-root

cd ~/xray_server_api
sudo cat <<EOF > /etc/systemd/system/xray_api.service
[Unit]
Description=Xray API
After=network.target

[Service]
Type=simple
User=$current_os_user
WorkingDirectory=/root/xray_server_api
ExecStart=/bin/bash -c 'cd /root/xray_server_api/ && $(poetry env info --executable) -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
cd

echo "$Orange" | sed 's/\$//g'
echo "Installing XRAY (XTLS-Reality)"
echo "............................................................"
echo "$Defaul_color" | sed 's/\$//g'

echo -e "${Green}\nEnter server Domain Name:${Default}"
echo -e "Just press ENTER to use the default domain name [${Blue}example.com${Default}]"
read -p "Domain Name: " domain_name
if [ -z "$domain_name" ]; then
    domain_name="example.com"
fi

# Запрос названия страны
echo -e "${Green}\nEnter server country name (e.g., 'Estonia'):${Default}"
read -p "Country Name: " server_country
if [ -z "$server_country" ]; then
    server_country="Estonia"  # Значение по умолчанию, если ничего не введено
fi

# Запрос кода страны
echo -e "${Green}\nEnter server country code (e.g., 'EE'):${Default}"
read -p "Country Code: " server_country_code
if [ -z "$server_country_code" ]; then
    server_country_code="EE"  # Значение по умолчанию, если ничего не введено
fi

site_url="dl.google.com"
config_prefix="VPNizator"

#install xray
bash -c "$(curl -L https://raw.githubusercontent.com/Ardgellan/XTLS_Reality_Server/main/install-release.sh)" @ install

# To increase performance, you can configure
# Bottleneck Bandwidth and
# Round-trip propagation time (BBR) congestion control algorithm on the server
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p

# execute /usr/local/bin/xray x25519
# and get public and private keys by splitting lines output and
# remove "Private key: " and "Public key: " from output
# and save it to variables
x25519_keys=$(sudo /usr/local/bin/xray x25519)
x25519_private_key=$(echo "$x25519_keys" | sed -n 1p | sed 's/Private key: //g')
x25519_public_key=$(echo "$x25519_keys" | sed -n 2p | sed 's/Public key: //g')
echo "$x25519_keys" | sed 's/\$//g'



#get short id by using openssl
short_id=$(sudo openssl rand -hex 8)

# configure xray
# sudo cat <<EOF > /usr/local/etc/xray/config.json
# {
#     "log": {
#         "loglevel": "info"
#     },
#     "routing": {
#         "rules": [],
#         "domainStrategy": "AsIs"
#     },
#     "inbounds": [
#         {
#             "port": 443,
#             "protocol": "vless",
#             "tag": "vless_tls",
#             "settings": {
#                 "clients": [],
#                 "decryption": "none"
#             },
#             "streamSettings": {
#                 "network": "tcp",
#                 "security": "reality",
#                 "realitySettings": {
#                     "show": false,
#                     "dest": "$site_url:443",
#                     "xver": 0,
#                     "serverNames": [
#                         "$site_url"
#                     ],
#                     "privateKey": "$x25519_private_key",
#                     "minClientVer": "",
#                     "maxClientVer": "",
#                     "maxTimeDiff": 0,
#                     "shortIds": [
#                         "$short_id"
#                     ]
#                 }
#             },
#             "sniffing": {
#                 "enabled": true,
#                 "destOverride": [
#                     "http",
#                     "tls"
#                 ]
#             }
#         }
#     ],
#     "outbounds": [
#         {
#             "protocol": "freedom",
#             "tag": "direct"
#         },
#         {
#             "protocol": "blackhole",
#             "tag": "block"
#         }
#     ]
# }
# EOF

sudo cat <<EOF > /usr/local/etc/xray/config.json
{
    "log": {
        "loglevel": "info",
        "access": "/var/log/xray/access.log",
        "error": "/var/log/xray/error.log"
    },
    "routing": {
        "rules": [
            {
                "type": "field",
                "protocol": ["bittorrent"],
                "outboundTag": "block"
                "log": true
            },
            {
                "type": "field",
                "ip": ["geoip:private"],
                "outboundTag": "block"
                "log": true
            }
        ],
        "domainStrategy": "AsIs"
    },
    "inbounds": [
        {
            "port": 443,
            "protocol": "vless",
            "tag": "vless_tls",
            "settings": {
                "clients": [],
                "decryption": "none"
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "show": false,
                    "dest": "$site_url:443",
                    "xver": 0,
                    "serverNames": [
                        "$site_url"
                    ],
                    "privateKey": "$x25519_private_key",
                    "minClientVer": "1.8.0",
                    "maxClientVer": "",
                    "maxTimeDiff": 0,
                    "shortIds": [
                        "$short_id"
                    ]
                }
            },
            "sniffing": {
                "enabled": true,
                "destOverride": [
                    "http",
                    "tls"
                ]
            }
        }
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "tag": "direct"
        },
        {
            "protocol": "blackhole",
            "tag": "block"
        }
    ]
}
EOF

# enable and start bot service
systemctl daemon-reload
systemctl enable xray_api.service
systemctl start xray_api.service
systemctl enable xray.service
systemctl restart xray.service

# configure xray_api .env file
sudo cat <<EOF > ~/xray_server_api/app/data/.env

XRAY_DOMAIN_NAME = "$domain_name"
SERVER_COUNTRY = "$server_country"
SERVER_COUNTRY_CODE = "$server_country_code"
XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
USER_CONFIGS_PREFIX = "$config_prefix"
XRAY_PRIVATEKEY = "$x25519_private_key"
XRAY_PUBLICKEY = "$x25519_public_key"
XRAY_SHORTID = "$short_id"
XRAY_SNI = "$site_url"
EOF

echo "Установка завершена!"