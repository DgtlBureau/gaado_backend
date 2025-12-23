#!/usr/bin/env python3
"""
Прямой тест facebook-scraper для диагностики проблем
"""
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from facebook_scraper import get_posts, get_profile
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_get_posts(username: str, use_cookies: bool = True):
    """Тест получения постов"""
    print(f"\n{'='*70}")
    print(f"🧪 Тест получения постов для: {username}")
    print(f"{'='*70}\n")
    
    cookies_file = "cookies.txt" if use_cookies else None
    
    try:
        # Современный User-Agent для обхода блокировок Facebook
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        call_kwargs = {
            "pages": 1,
            "options": {
                "user_agent": user_agent
            }
        }
        
        if cookies_file:
            import os
            if os.path.exists(cookies_file):
                call_kwargs["cookies"] = cookies_file
                print(f"✅ Используем cookies из: {cookies_file}")
            else:
                print(f"⚠️ Файл cookies не найден: {cookies_file}")
        else:
            print("ℹ️ Запрос без cookies")
        
        print(f"✅ Используем User-Agent: {user_agent[:60]}...")
        
        print(f"\n📋 Параметры запроса: {list(call_kwargs.keys())}")
        print(f"Вызываем: get_posts('{username}', **{call_kwargs})\n")
        
        # Создаем генератор
        print("1️⃣ Создаем генератор...")
        posts_generator = get_posts(username, **call_kwargs)
        print("✅ Генератор создан")
        
        # Пробуем получить посты
        print("\n2️⃣ Итерируем по генератору...")
        posts_list = []
        
        try:
            for i, post in enumerate(posts_generator):
                posts_list.append(post)
                post_id = post.get('post_id', 'N/A')
                text_preview = (post.get('text', '') or post.get('post_text', ''))[:50]
                print(f"   ✅ Пост #{i+1}: post_id={post_id}, text='{text_preview}...'")
                # Останавливаемся после первого поста для теста
                if i == 0:
                    break
        except AssertionError as e:
            print(f"\n❌ AssertionError при итерации:")
            print(f"   {repr(e)}")
            print(f"   {str(e)}")
            return None
        except StopIteration:
            print("   ℹ️ Генератор завершился (StopIteration)")
        except Exception as e:
            print(f"\n❌ Ошибка при итерации: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        print(f"\n📊 Результат: получено {len(posts_list)} постов")
        
        if posts_list:
            print("\n✅ ТЕСТ ПРОЙДЕН! Посты получены успешно.")
            return posts_list
        else:
            print("\n⚠️ Генератор вернул пустой список")
            print("   Возможные причины:")
            print("   - Страница недоступна или требует авторизации")
            print("   - Неправильный username")
            print("   - Facebook блокирует запросы")
            print("   - Страница не имеет публичных постов")
            return None
            
    except AssertionError as e:
        print(f"\n❌ AssertionError при вызове get_posts:")
        print(f"   {repr(e)}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    
    username = sys.argv[1] if len(sys.argv) > 1 else "premierbankso"
    use_cookies = "--no-cookies" not in sys.argv
    
    print("="*70)
    print("ПРЯМОЙ ТЕСТ FACEBOOK-SCRAPER")
    print("="*70)
    
    result = test_get_posts(username, use_cookies)
    
    if result:
        print(f"\n✅ Успешно получено {len(result)} постов")
        sys.exit(0)
    else:
        print("\n❌ Тест не прошел")
        sys.exit(1)

