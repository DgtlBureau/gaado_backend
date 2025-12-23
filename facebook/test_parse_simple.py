#!/usr/bin/env python3
"""
Простой тест парсинга комментариев
"""
import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from facebook_client import FacebookScraperClient
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def main():
    url = "https://www.facebook.com/premierbankso/posts/pfbid08QZAvQEGniaWzLPvfMGhtebL8ANKEW43weHKW3o9si8Jr9ZGEXSkfPxiHFk5oAR1l"
    
    print("=" * 80)
    print("🧪 Тест парсинга комментариев с Facebook")
    print("=" * 80)
    print(f"URL: {url}")
    print("-" * 80)
    
    try:
        # Проверяем наличие cookies
        cookies_file = "cookies.txt"
        if os.path.exists(cookies_file):
            print(f"✅ Найден файл cookies: {cookies_file}")
            client = FacebookScraperClient(cookies=cookies_file)
        else:
            print("⚠️  Файл cookies.txt не найден, используем клиент без cookies")
            client = FacebookScraperClient()
        
        print("\n📥 Загружаем HTML со страницы...")
        result = await client.fetch_and_parse_comments_from_url(url, limit=100)
        
        comments = result.get('comments', [])
        print(f"\n✅ Успешно!")
        print(f"   Найдено комментариев: {len(comments)}")
        print(f"   Размер HTML: {result.get('html_size', 0):,} символов")
        
        if comments:
            print(f"\n💬 Первые {min(10, len(comments))} комментариев:")
            print("-" * 80)
            for i, comment in enumerate(comments[:10], 1):
                author = comment.get('author', 'Аноним')
                text = comment.get('text', '')
                likes = comment.get('likes', 0)
                time = comment.get('time', '')
                
                print(f"\n{i}. 👤 {author}")
                if text:
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"   💭 {preview}")
                if likes > 0:
                    print(f"   ❤️  {likes} лайков")
                if time:
                    print(f"   🕐 {time}")
        else:
            print("\n⚠️ Комментарии не найдены")
            if result.get('error'):
                print(f"   Ошибка: {result.get('error')}")
            print("\n💡 Возможные причины:")
            print("   - Facebook блокирует запросы без cookies")
            print("   - Структура HTML изменилась")
            print("   - Комментарии требуют авторизации")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

