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

current_os_user=$(whoami)

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

# Расширение системы, если она была минимизирована
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

#enable and start bot service
systemctl daemon-reload
systemctl enable xray_api.service
systemctl start xray_api.service

echo "Установка завершена!"
