#!/usr/bin/env python3
"""
Тест парсинга комментариев через браузер (Playwright) с рендерингом JavaScript
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from facebook.facebook_client import FacebookScraperClient
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def main():
    url = "https://www.facebook.com/premierbankso/posts/pfbid08QZAvQEGniaWzLPvfMGhtebL8ANKEW43weHKW3o9si8Jr9ZGEXSkfPxiHFk5oAR1l"
    
    print("=" * 80)
    print("🌐 Тест парсинга комментариев через БРАУЗЕР (Playwright)")
    print("=" * 80)
    print(f"URL: {url}")
    print("-" * 80)
    print("\n⚠️  ВАЖНО: Этот метод использует реальный браузер для рендеринга JavaScript")
    print("   Это позволяет извлекать комментарии, которые загружаются динамически.")
    print("   Первый запуск может занять время (установка браузера).\n")
    
    try:
        # Проверяем наличие cookies
        cookies_file = "facebook/cookies.txt"
        if os.path.exists(cookies_file):
            print(f"✅ Найден файл cookies: {cookies_file}")
            client = FacebookScraperClient(cookies=cookies_file)
        else:
            print("⚠️  Файл facebook/cookies.txt не найден, используем клиент без cookies")
            client = FacebookScraperClient()
        
        print("\n📥 Загружаем страницу через браузер...")
        print("   (Это может занять 10-30 секунд)")
        
        result = await client.fetch_and_parse_comments_with_browser(
            url, 
            limit=50,  # Запрашиваем 50 комментариев
            wait_time=10  # Увеличиваем время ожидания до 10 секунд для загрузки большего количества комментариев
        )
        
        comments = result.get('comments', [])
        print(f"\n✅ Успешно!")
        print(f"   Метод: {result.get('method', 'N/A')}")
        print(f"   Найдено комментариев: {len(comments)}")
        print(f"   Размер HTML: {result.get('html_size', 0):,} символов")
        
        if comments:
            print(f"\n💬 Всего найдено {len(comments)} комментариев:")
            print("-" * 80)
            # Показываем все комментарии (или первые 20 для краткости)
            display_count = min(20, len(comments))
            for i, comment in enumerate(comments[:display_count], 1):
                author = comment.get('author', 'Аноним') or 'Аноним'
                text = comment.get('text', '') or ''
                likes = comment.get('likes', 0)
                time = comment.get('time', '') or ''
                
                print(f"\n{i}. 👤 {author}")
                if text:
                    # Показываем полный текст или первые 300 символов
                    preview = text[:300] + "..." if len(text) > 300 else text
                    print(f"   💭 {preview}")
                if likes > 0:
                    print(f"   ❤️  {likes} лайков")
                if time:
                    print(f"   🕐 {time}")
            
            if len(comments) > display_count:
                print(f"\n... и еще {len(comments) - display_count} комментариев (см. логи для полного списка)")
            
            # Сохраняем комментарии в файл для удобства
            import json
            output_file = "scraped_comments.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "url": url,
                        "scraped_at": result.get('fetched_at'),
                        "total_count": len(comments),
                        "comments": comments
                    }, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Комментарии сохранены в файл: {output_file}")
            except Exception as e:
                print(f"\n⚠️  Не удалось сохранить в файл: {e}")
        else:
            print("\n⚠️ Комментарии не найдены")
            print("\n💡 Возможные причины:")
            print("   - Комментарии еще не загрузились (увеличьте wait_time)")
            print("   - Требуется авторизация (проверьте cookies.txt)")
            print("   - Структура HTML изменилась")
        
        print("\n" + "=" * 80)
        print("✅ Тест завершен!")
        print("=" * 80)
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("\n📦 Установите Playwright:")
        print("   pip install playwright")
        print("   playwright install chromium")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

