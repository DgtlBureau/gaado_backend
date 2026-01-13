#!/bin/bash

# Скрипт запуска Gaado Backend

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "Проверка зависимостей..."
pip install -q -r requirements.txt

# Запуск сервера
echo "Запуск сервера на http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
