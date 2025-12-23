#!/usr/bin/env python3
"""
Быстрый тест Facebook скраппера через localhost
"""
import httpx
import asyncio
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"


async def test_facebook_scraper(page_username: str = "premierbankso"):
    """Тестирование Facebook скраппера"""
    print("=" * 70)
    print(f"🧪 Тестирование Facebook Scraper для страницы: {page_username}")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Тест 1: Получение данных через GET
            print(f"\n1️⃣ GET запрос: /facebook/page/{page_username}")
            print("-" * 70)
            response = await client.get(f"{API_BASE_URL}/facebook/page/{page_username}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Успешно!")
                display_results(data.get("data", {}))
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(response.text)
                return
            
            # Тест 2: Тестовый эндпоинт
            print(f"\n\n2️⃣ POST запрос: /facebook/test")
            print("-" * 70)
            response = await client.post(
                f"{API_BASE_URL}/facebook/test",
                json={"page_username": page_username}
            )
            
            if response.status_code == 200:
                test_data = response.json()
                print("✅ Тест пройден!")
                if test_data.get("success"):
                    print(f"   Сообщение: {test_data.get('message', 'N/A')}")
                    results = test_data.get("test_results", {})
                    if results.get("latest_post"):
                        post = results["latest_post"]
                        print(f"   Пост ID: {post.get('post_id', 'N/A')}")
                        print(f"   Лайки: {post.get('likes', 0)}")
                        print(f"   Комментарии: {post.get('comments', 0)}")
            else:
                print(f"⚠️ Статус: {response.status_code}")
                print(response.text)
            
            print("\n" + "=" * 70)
            print("✅ Тестирование завершено!")
            print("=" * 70)
            
        except httpx.ConnectError:
            print("\n❌ Ошибка подключения!")
            print("   Убедитесь, что сервер запущен:")
            print("   uvicorn main:app --reload")
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


def display_results(data: dict):
    """Красивый вывод результатов"""
    page_info = data.get("page_info", {})
    post = data.get("post", {})
    reactions = data.get("reactions", {})
    comments = data.get("comments", {})
    
    print(f"\n📄 Страница: {page_info.get('name', page_info.get('username', 'N/A'))}")
    print(f"   Username: {page_info.get('username', 'N/A')}")
    print(f"   Подписчиков: {page_info.get('fan_count', 'N/A')}")
    
    if post:
        print(f"\n📝 Последний пост:")
        print(f"   ID: {post.get('post_id', 'N/A')}")
        text = post.get('text', '')
        if text:
            preview = text[:150] + "..." if len(text) > 150 else text
            print(f"   Текст: {preview}")
        print(f"   Дата: {post.get('time', 'N/A')}")
        print(f"   Лайки: {post.get('likes', 0)}")
        print(f"   Комментарии: {post.get('comments', 0)}")
        print(f"   Репосты: {post.get('shares', 0)}")
        
        if reactions:
            print(f"\n❤️ Реакции:")
            print(f"   Всего: {reactions.get('total_reactions', 0)}")
            reactions_by_type = reactions.get('reactions_by_type', {})
            for reaction_type, count in reactions_by_type.items():
                if count > 0:
                    print(f"   {reaction_type}: {count}")
        
        if comments:
            print(f"\n💬 Комментарии:")
            print(f"   Всего: {comments.get('total_count', 0)}")
            sample_comments = comments.get('comments', [])[:3]
            if sample_comments:
                print(f"\n   Первые {len(sample_comments)} комментария:")
                for i, comment in enumerate(sample_comments, 1):
                    print(f"   {i}. {comment.get('author', 'Аноним')}: {comment.get('text', '')[:60]}...")
                    print(f"      Лайков: {comment.get('likes', 0)}")
    else:
        error = data.get('error', 'Неизвестная ошибка')
        print(f"\n⚠️ {error}")


if __name__ == "__main__":
    import sys
    
    # Можно передать username как аргумент
    page_username = sys.argv[1] if len(sys.argv) > 1 else "premierbankso"
    
    print("\n⚠️ Убедитесь, что сервер запущен:")
    print("   uvicorn main:app --reload")
    print("\n")
    
    asyncio.run(test_facebook_scraper(page_username))

