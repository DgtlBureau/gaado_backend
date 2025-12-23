#!/usr/bin/env python3
"""
Тестовый файл для локального запуска Hugging Face клиента
"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если есть)
load_dotenv()

# Добавляем путь к корню проекта для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from huggingface.huggingface_client import HuggingFaceClient


def main():
    """Главная функция для запуска теста"""
    print("=" * 70)
    print("🚀 Тестирование Hugging Face Client")
    print("=" * 70)
    
    # Проверка переменных окружения
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        print("\n⚠️  ВНИМАНИЕ: HF_API_KEY не установлен!")
        print("   Установите переменную окружения:")
        print("   export HF_API_KEY='your_api_key_here'")
        print("\n   Или создайте файл .env в корне проекта:")
        print("   HF_API_KEY=your_api_key_here")
        print("\n   Получить API ключ можно здесь:")
        print("   https://huggingface.co/settings/tokens")
        print("=" * 70)
        return
    
    print(f"\n✅ HF_API_KEY найден: {api_key[:10]}...")
    
    default_model = os.getenv("HF_DEFAULT_MODEL", "Qwen/Qwen2.5-7B-Instruct:together")
    print(f"✅ Модель по умолчанию: {default_model}")
    print("=" * 70)
    
    try:
        client = HuggingFaceClient()
        
        if not client.is_available():
            print("\n❌ Клиент не доступен. Проверьте HF_API_KEY в переменных окружения.")
            return
        
        prompt = "What is the capital of France?"
        print(f"\n📝 Запрос: {prompt}")
        print("-" * 70)
        
        response = client.simple_chat(prompt)
        print(f"✅ Ответ: {response}")
        
        print("\n" + "=" * 70)
        print("✅ Тест завершен успешно!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

