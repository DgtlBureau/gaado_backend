#!/bin/zsh

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Виртуальное окружение не найдено. Создайте его командой: python3 -m venv venv"
    exit 1
fi

# Проверка и установка зависимостей при необходимости
echo "Проверка зависимостей..."
python3 -c "from google import genai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Установка google-genai..."
    pip install google-genai
fi

python3 -c "import openpyxl" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Установка openpyxl (опционально, для поддержки Excel)..."
    pip install openpyxl || echo "openpyxl не установлен (будет использоваться только CSV)"
fi

echo ""
echo "Запуск обработки комментариев через Gemini API..."
echo ""

python3 ./complains_processing/process_risks.py
