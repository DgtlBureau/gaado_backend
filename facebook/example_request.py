"""
Пример использования API для тестирования
"""
import httpx
import asyncio


async def test_process():
    """Тестовый запрос к API"""
    url = "http://localhost:8000/process"
    
    data = {
        "text": "I love this product! It's amazing and works perfectly.",
        "metadata": {
            "source": "example.com",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, timeout=30.0)
            response.raise_for_status()
            print("Response:", response.json())
        except Exception as e:
            print(f"Error: {e}")


async def test_health():
    """Проверка здоровья сервиса"""
    url = "http://localhost:8000/health"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            print("Health check:", response.json())
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("Testing health endpoint...")
    asyncio.run(test_health())
    
    print("\nTesting process endpoint...")
    asyncio.run(test_process())

