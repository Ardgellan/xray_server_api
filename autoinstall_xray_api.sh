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

uvicorn app.main:app --reload

echo "Установка завершена!"
