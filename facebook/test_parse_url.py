#!/usr/bin/env python3
"""
Тестовый скрипт для парсинга комментариев с URL страницы Facebook
"""
import asyncio
import sys
from facebook_client import FacebookScraperClient
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_parse_url(url: str):
    """Тестирование парсинга комментариев с URL"""
    print("=" * 80)
    print(f"🧪 Тестирование парсинга комментариев с URL")
    print("=" * 80)
    print(f"URL: {url}")
    print("-" * 80)
    
    try:
        # Создаем клиент с cookies если есть
        import os
        cookies_file = os.getenv("FACEBOOK_COOKIES_FILE", "cookies.txt")
        if os.path.exists(cookies_file):
            logger.info(f"Используем cookies из файла: {cookies_file}")
            client = FacebookScraperClient(cookies=cookies_file)
        else:
            logger.warning("Cookies не найдены, используем клиент без cookies")
            client = FacebookScraperClient()
        
        # Загружаем и парсим комментарии
        print("\n📥 Загружаем HTML со страницы...")
        result = await client.fetch_and_parse_comments_from_url(url, limit=100)
        
        print(f"\n✅ Успешно обработано!")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Размер HTML: {result.get('html_size', 0):,} символов")
        print(f"   Найдено комментариев: {result.get('total_count', 0)}")
        print(f"   Время загрузки: {result.get('fetched_at', 'N/A')}")
        
        comments = result.get('comments', [])
        if comments:
            print(f"\n💬 Комментарии ({len(comments)}):")
            print("-" * 80)
            for i, comment in enumerate(comments[:10], 1):  # Показываем первые 10
                author = comment.get('author', 'Аноним')
                text = comment.get('text', '')
                likes = comment.get('likes', 0)
                time = comment.get('time', '')
                
                print(f"\n{i}. 👤 {author}")
                if text:
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"   💭 {preview}")
                if likes > 0:
                    print(f"   ❤️  {likes} лайков")
                if time:
                    print(f"   🕐 {time}")
                print("-" * 80)
            
            if len(comments) > 10:
                print(f"\n... и еще {len(comments) - 10} комментариев")
        else:
            print("\n⚠️ Комментарии не найдены")
            if result.get('error'):
                print(f"   Ошибка: {result.get('error')}")
        
        print("\n" + "=" * 80)
        print("✅ Тестирование завершено!")
        print("=" * 80)
        
        return result
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("   Установите необходимые библиотеки:")
        print("   pip install httpx beautifulsoup4")
        return None
    except ValueError as e:
        print(f"\n❌ Ошибка валидации: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # URL по умолчанию или из аргументов командной строки
    default_url = "https://www.facebook.com/premierbankso/posts/pfbid08QZAvQEGniaWzLPvfMGhtebL8ANKEW43weHKW3o9si8Jr9ZGEXSkfPxiHFk5oAR1l"
    
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    
    print("\n⚠️ Убедитесь, что:")
    print("   1. Установлены зависимости: pip install httpx beautifulsoup4")
    print("   2. Файл cookies.txt существует (опционально, но рекомендуется)")
    print("\n")
    
    asyncio.run(test_parse_url(url))

