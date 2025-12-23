#!/usr/bin/env python3
"""
Простой тест парсинга комментариев только через HTML (без facebook-scraper)
"""
import asyncio
import sys
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ BeautifulSoup не установлен. Установите: pip install beautifulsoup4")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("❌ httpx не установлен. Установите: pip install httpx")
    sys.exit(1)


def load_cookies_dict(cookies_file: str) -> Dict[str, str]:
    """Загрузить cookies из файла"""
    cookies_dict = {}
    if not os.path.exists(cookies_file):
        return cookies_dict
    
    try:
        with open(cookies_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 7:
                    cookie_name = parts[5]
                    cookie_value = parts[6] if len(parts) > 6 else ''
                    cookies_dict[cookie_name] = cookie_value
    except Exception as e:
        print(f"⚠️  Не удалось загрузить cookies: {e}")
    
    return cookies_dict


def parse_comments_from_html(html_content: str, limit: int = 100) -> Dict[str, Any]:
    """Парсинг комментариев из HTML"""
    if not html_content or not html_content.strip():
        return {"comments": [], "total_count": 0}
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        comments = []
        
        # Различные стратегии поиска комментариев
        comment_elements = []
        
        # Вариант 1: Поиск по data-ft
        comment_elements = soup.find_all(attrs={"data-ft": re.compile(r".*top_level_post_id.*")})
        
        # Вариант 2: Поиск по классам
        if not comment_elements:
            comment_elements = soup.find_all('div', class_=re.compile(r'.*comment.*', re.I))
        
        # Вариант 3: Поиск по data-testid
        if not comment_elements:
            comment_elements = soup.find_all('div', attrs={"data-testid": re.compile(r".*comment.*", re.I)})
        
        # Вариант 4: Поиск по role="article"
        if not comment_elements:
            comment_elements = soup.find_all('div', role="article")
        
        # Вариант 5: Поиск по data-sigil
        if not comment_elements:
            comment_elements = soup.find_all(attrs={"data-sigil": re.compile(r".*comment.*", re.I)})
        
        print(f"   Найдено {len(comment_elements)} потенциальных элементов комментариев")
        
        for idx, element in enumerate(comment_elements[:limit]):
            try:
                comment_data = extract_comment_data(element)
                if comment_data and comment_data.get("text"):
                    comments.append(comment_data)
            except Exception as e:
                continue
        
        return {
            "comments": comments,
            "total_count": len(comments)
        }
        
    except Exception as e:
        return {
            "comments": [],
            "total_count": 0,
            "error": str(e)
        }


def extract_comment_data(element) -> Optional[Dict[str, Any]]:
    """Извлечь данные одного комментария"""
    try:
        comment_data = {}
        
        # Извлечение текста
        text_selectors = [
            'div[data-testid="comment"]',
            '.userContent',
            '[data-sigil="comment-body"]',
            '.comment-body',
            'span[dir="auto"]',
        ]
        
        text = None
        for selector in text_selectors:
            text_elem = element.select_one(selector)
            if text_elem:
                text = text_elem.get_text(strip=True)
                if text:
                    break
        
        if not text:
            text_parts = []
            for text_node in element.find_all(string=True):
                parent = text_node.parent
                if parent and parent.name not in ['a', 'button', 'script', 'style']:
                    text_part = text_node.strip()
                    if text_part:
                        text_parts.append(text_part)
            text = ' '.join(text_parts).strip()
        
        comment_data["text"] = text or ""
        
        # Извлечение автора
        author_selectors = [
            'a[role="link"]',
            'strong a',
            'h3 a',
            '[data-hovercard-prefer-more-content-show="1"]',
            'a[href*="/user/"]',
            'a[href*="/profile.php"]',
        ]
        
        author = None
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                if author:
                    break
        
        comment_data["author"] = author or ""
        
        # Извлечение лайков
        likes = 0
        likes_selectors = [
            '[aria-label*="Like"]',
            '[data-sigil="reactions-count"]',
            '.like-count',
        ]
        
        for selector in likes_selectors:
            likes_elem = element.select_one(selector)
            if likes_elem:
                likes_text = likes_elem.get_text(strip=True)
                likes_match = re.search(r'(\d+)', likes_text.replace(',', '').replace('.', ''))
                if likes_match:
                    try:
                        likes = int(likes_match.group(1))
                        break
                    except ValueError:
                        pass
        
        comment_data["likes"] = likes
        
        return comment_data if comment_data.get("text") else None
        
    except Exception:
        return None


async def fetch_and_parse(url: str, limit: int = 100):
    """Загрузить HTML и распарсить комментарии"""
    print(f"\n📥 Загружаем HTML со страницы...")
    
    cookies_file = "cookies.txt"
    cookies_dict = load_cookies_dict(cookies_file)
    
    # Пробуем мобильную версию Facebook (часто более доступна)
    mobile_url = url.replace("www.facebook.com", "m.facebook.com")
    print(f"   Пробуем мобильную версию: {mobile_url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Пробуем сначала мобильную версию
            try:
                response = await client.get(mobile_url, headers=headers, cookies=cookies_dict)
                if response.status_code == 200:
                    print(f"   ✅ Используем мобильную версию")
                else:
                    print(f"   ⚠️  Мобильная версия вернула {response.status_code}, пробуем обычную")
                    response = await client.get(url, headers=headers, cookies=cookies_dict)
            except:
                # Если мобильная не работает, пробуем обычную
                print(f"   ⚠️  Мобильная версия не доступна, пробуем обычную")
                response = await client.get(url, headers=headers, cookies=cookies_dict)
            
            response.raise_for_status()
            
            html_content = response.text
            print(f"   ✅ HTML загружен: {len(html_content):,} символов")
            
            # Парсим комментарии
            print(f"\n🔍 Парсим комментарии...")
            result = parse_comments_from_html(html_content, limit=limit)
            
            result["url"] = url
            result["html_size"] = len(html_content)
            result["fetched_at"] = datetime.now().isoformat()
            
            return result
            
    except httpx.HTTPStatusError as e:
        print(f"   ❌ HTTP ошибка: {e.response.status_code}")
        raise
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        raise


async def main():
    url = "https://www.facebook.com/premierbankso/posts/pfbid08QZAvQEGniaWzLPvfMGhtebL8ANKEW43weHKW3o9si8Jr9ZGEXSkfPxiHFk5oAR1l"
    
    print("=" * 80)
    print("🧪 Тест парсинга комментариев с Facebook")
    print("=" * 80)
    print(f"URL: {url}")
    print("-" * 80)
    
    if os.path.exists("cookies.txt"):
        print("✅ Найден файл cookies.txt")
    else:
        print("⚠️  Файл cookies.txt не найден (может потребоваться для доступа)")
    
    try:
        result = await fetch_and_parse(url, limit=100)
        
        comments = result.get('comments', [])
        print(f"\n✅ Успешно обработано!")
        print(f"   Найдено комментариев: {len(comments)}")
        print(f"   Размер HTML: {result.get('html_size', 0):,} символов")
        
        if comments:
            print(f"\n💬 Первые {min(10, len(comments))} комментариев:")
            print("-" * 80)
            for i, comment in enumerate(comments[:10], 1):
                author = comment.get('author', 'Аноним')
                text = comment.get('text', '')
                likes = comment.get('likes', 0)
                
                print(f"\n{i}. 👤 {author}")
                if text:
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"   💭 {preview}")
                if likes > 0:
                    print(f"   ❤️  {likes} лайков")
        else:
            print("\n⚠️ Комментарии не найдены")
            if result.get('error'):
                print(f"   Ошибка: {result.get('error')}")
            print("\n💡 Возможные причины:")
            print("   - Facebook блокирует запросы без cookies")
            print("   - Структура HTML изменилась")
            print("   - Комментарии требуют авторизации")
            print("   - Комментарии загружаются динамически через JavaScript")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

