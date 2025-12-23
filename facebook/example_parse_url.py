#!/usr/bin/env python3
"""
Пример использования парсера комментариев с URL страницы Facebook
"""
import asyncio
import httpx
import json


async def parse_url_via_api(url: str):
    """Парсинг комментариев через API"""
    api_url = "http://localhost:8000/facebook/parse-url"
    
    print("=" * 80)
    print("🌐 Парсинг комментариев через API")
    print("=" * 80)
    print(f"URL: {url}")
    print("-" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                api_url,
                json={"url": url, "limit": 100}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("data", {})
                    comments = result.get("comments", [])
                    
                    print(f"\n✅ Успешно обработано!")
                    print(f"   Найдено комментариев: {len(comments)}")
                    print(f"   Размер HTML: {result.get('html_size', 0):,} символов")
                    
                    if comments:
                        print(f"\n💬 Первые {min(5, len(comments))} комментариев:")
                        print("-" * 80)
                        for i, comment in enumerate(comments[:5], 1):
                            author = comment.get('author', 'Аноним')
                            text = comment.get('text', '')
                            likes = comment.get('likes', 0)
                            
                            print(f"\n{i}. 👤 {author}")
                            if text:
                                preview = text[:150] + "..." if len(text) > 150 else text
                                print(f"   💭 {preview}")
                            if likes > 0:
                                print(f"   ❤️  {likes} лайков")
                            print("-" * 80)
                else:
                    print(f"\n❌ Ошибка: {data.get('error', 'Неизвестная ошибка')}")
            else:
                print(f"\n❌ HTTP ошибка: {response.status_code}")
                print(response.text)
                
        except httpx.ConnectError:
            print("\n❌ Не удалось подключиться к API")
            print("   Убедитесь, что сервер запущен:")
            print("   uvicorn main:app --reload")
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")


async def parse_url_direct(url: str):
    """Прямой парсинг комментариев (без API)"""
    from facebook_client import FacebookScraperClient
    import os
    
    print("=" * 80)
    print("🔧 Прямой парсинг комментариев")
    print("=" * 80)
    print(f"URL: {url}")
    print("-" * 80)
    
    try:
        # Создаем клиент с cookies если есть
        cookies_file = os.getenv("FACEBOOK_COOKIES_FILE", "cookies.txt")
        if os.path.exists(cookies_file):
            print(f"📁 Используем cookies из файла: {cookies_file}")
            client = FacebookScraperClient(cookies=cookies_file)
        else:
            print("⚠️  Cookies не найдены, используем клиент без cookies")
            client = FacebookScraperClient()
        
        # Загружаем и парсим комментарии
        print("\n📥 Загружаем HTML со страницы...")
        result = await client.fetch_and_parse_comments_from_url(url, limit=100)
        
        comments = result.get('comments', [])
        print(f"\n✅ Успешно обработано!")
        print(f"   Найдено комментариев: {len(comments)}")
        print(f"   Размер HTML: {result.get('html_size', 0):,} символов")
        
        if comments:
            print(f"\n💬 Первые {min(5, len(comments))} комментариев:")
            print("-" * 80)
            for i, comment in enumerate(comments[:5], 1):
                author = comment.get('author', 'Аноним')
                text = comment.get('text', '')
                likes = comment.get('likes', 0)
                
                print(f"\n{i}. 👤 {author}")
                if text:
                    preview = text[:150] + "..." if len(text) > 150 else text
                    print(f"   💭 {preview}")
                if likes > 0:
                    print(f"   ❤️  {likes} лайков")
                print("-" * 80)
        else:
            print("\n⚠️ Комментарии не найдены")
            if result.get('error'):
                print(f"   Ошибка: {result.get('error')}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # URL по умолчанию
    url = "https://www.facebook.com/premierbankso/posts/pfbid08QZAvQEGniaWzLPvfMGhtebL8ANKEW43weHKW3o9si8Jr9ZGEXSkfPxiHFk5oAR1l"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    # Можно выбрать метод: "api" или "direct"
    method = sys.argv[2] if len(sys.argv) > 2 else "direct"
    
    print("\n" + "=" * 80)
    print("📋 Инструкция:")
    print("=" * 80)
    print("1. Через API (требует запущенный сервер):")
    print("   python example_parse_url.py <URL> api")
    print("\n2. Прямой парсинг (без API):")
    print("   python example_parse_url.py <URL> direct")
    print("\n" + "=" * 80 + "\n")
    
    if method == "api":
        asyncio.run(parse_url_via_api(url))
    else:
        asyncio.run(parse_url_direct(url))

