"""
Facebook Scraper Client
Для получения данных с публичных страниц Facebook без использования API
Использует библиотеку facebook-scraper
"""
import asyncio
import logging
import re
from functools import partial
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from facebook_scraper import get_posts, get_profile
except ImportError:
    logger.error("facebook-scraper не установлен. Установите: pip install facebook-scraper")
    raise

try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.warning("BeautifulSoup не установлен. Парсинг HTML может не работать. Установите: pip install beautifulsoup4")
    BeautifulSoup = None

try:
    import httpx
except ImportError:
    logger.warning("httpx не установлен. Загрузка HTML со страниц может не работать. Установите: pip install httpx")
    httpx = None

try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    logger.warning("Playwright не установлен. Рендеринг JavaScript не будет работать. Установите: pip install playwright && playwright install chromium")
    async_playwright = None


class FacebookScraperClient:
    """Клиент для работы с Facebook через скрейпинг"""
    
    def __init__(self, cookies: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            cookies: Путь к файлу с cookies (опционально, для обхода ограничений)
            user_agent: User-Agent для запросов (опционально)
        """
        self.cookies = cookies
        # Используем современный User-Agent по умолчанию, если не указан
        # Это важно, так как Facebook блокирует запросы с неправильным User-Agent
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    
    async def _get_posts_async(self, page_username: str, pages: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """
        Асинхронная обертка для get_posts
        
        Args:
            page_username: Username страницы
            pages: Количество страниц постов для получения
            **kwargs: Дополнительные параметры для get_posts
            
        Returns:
            Список постов
        """
        try:
            # Получаем event loop безопасным способом
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            logger.info(f"Начинаем получение постов для {page_username}, pages={pages}, cookies={'есть' if self.cookies else 'нет'}")
            
            # УПРОЩЕННЫЙ ЗАПРОС - убираем extra_info для отладки
            # Опции для получения комментариев и реакций - ОТКЛЮЧЕНО для отладки
            # ВАЖНО: User-Agent обязателен, иначе Facebook блокирует запросы
            options = {
                "user_agent": self.user_agent
            }
            logger.info(f"Используем User-Agent: {self.user_agent[:50]}...")
            
            # Параметры для get_posts - МИНИМАЛЬНЫЙ НАБОР
            def _get_posts():
                call_kwargs = {
                    "pages": pages,
                    # "extra_info": True,  # ОТКЛЮЧЕНО для отладки
                }
                
                # Добавляем cookies если есть
                if self.cookies:
                    call_kwargs["cookies"] = self.cookies
                    logger.info(f"Используем cookies из файла: {self.cookies}")
                
                # Добавляем options если есть
                if options:
                    call_kwargs["options"] = options
                
                # Добавляем дополнительные параметры из kwargs
                call_kwargs.update(kwargs)
                
                logger.info(f"Вызываем get_posts с параметрами: {list(call_kwargs.keys())}")
                
                # Вызываем get_posts с username как позиционным аргументом
                try:
                    logger.info(f"Создаем генератор get_posts для {page_username}")
                    posts_generator = get_posts(page_username, **call_kwargs)
                    logger.info(f"Генератор создан, начинаем итерацию...")
                    
                    # Пробуем получить хотя бы один пост
                    posts_list = []
                    try:
                        for i, post in enumerate(posts_generator):
                            posts_list.append(post)
                            logger.info(f"Получен пост #{i+1}: post_id={post.get('post_id', 'N/A')}")
                            # Останавливаемся после первого поста для теста
                            if i == 0:
                                break
                    except AssertionError as e:
                        logger.error(f"AssertionError при итерации постов: {e}")
                        logger.error(f"Полная ошибка: {repr(e)}")
                        raise
                    except StopIteration:
                        logger.warning("Генератор завершился (StopIteration)")
                    except Exception as e:
                        logger.error(f"Ошибка при итерации: {type(e).__name__}: {e}")
                        raise
                    
                    logger.info(f"Итого получено {len(posts_list)} постов из генератора")
                    if not posts_list:
                        logger.warning("⚠️ Генератор вернул пустой список. Возможные причины:")
                        logger.warning("  1. Страница недоступна или требует авторизации")
                        logger.warning("  2. Неправильный username")
                        logger.warning("  3. Facebook блокирует запросы (нужны cookies)")
                        logger.warning("  4. Страница не имеет публичных постов")
                    
                    return posts_list
                except AssertionError as e:
                    logger.error(f"AssertionError при получении постов: {e}")
                    logger.error(f"Полная ошибка: {repr(e)}")
                    logger.error(f"Это может означать, что страница {page_username} недоступна или не найдена")
                    raise
                except Exception as e:
                    logger.error(f"Исключение в _get_posts: {type(e).__name__}: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
            
            posts = await loop.run_in_executor(None, _get_posts)
            logger.info(f"✅ Успешно получено {len(posts)} постов со страницы {page_username}")
            if posts:
                logger.info(f"Первый пост: post_id={posts[0].get('post_id', 'N/A')}, text_length={len(posts[0].get('text', ''))}")
            return posts
        except AssertionError as e:
            error_msg = f"Не удалось извлечь посты со страницы {page_username}. Возможные причины: страница недоступна, приватная или требует авторизации. Ошибка: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except ValueError as e:
            # Пробрасываем ValueError как есть
            logger.error(f"Ошибка валидации при получении постов: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении постов со страницы {page_username}: {type(e).__name__}: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise ValueError(f"Не удалось получить посты со страницы {page_username}: {str(e)}")
    
    async def get_page_info(self, page_username: str) -> Dict[str, Any]:
        """
        Получить информацию о странице
        
        Args:
            page_username: Username страницы (например, 'premierbankso')
            
        Returns:
            Информация о странице
            
        Note:
            Если вы видите ошибку "Unable to extract top_post <class 'AssertionError'>" в логах,
            это означает, что библиотека не смогла найти верхний пост на странице. Это не критично
            и не прерывает выполнение, но может указывать на:
            - Страница не имеет публичных постов
            - Страница требует авторизации
            - Facebook изменил структуру HTML
            - Неверный username страницы
            
            Метод продолжит работу и вернет доступную информацию о странице.
        """
        try:
            # Получаем event loop безопасным способом
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            def _get_profile():
                # Библиотека facebook-scraper ожидает username как позиционный аргумент
                call_kwargs = {}
                if self.cookies:
                    call_kwargs["cookies"] = self.cookies
                
                profile = get_profile(page_username, **call_kwargs)
                
                # Проверяем, есть ли предупреждение о top_post
                # Если библиотека не смогла извлечь top_post, это не критично,
                # но может означать проблемы с доступом к странице
                if "top_post" not in profile or profile.get("top_post") is None:
                    logger.debug(f"top_post не найден для {page_username} - это нормально, если страница не имеет постов или требует авторизации")
                
                return profile
            
            profile = await loop.run_in_executor(None, _get_profile)
            logger.info(f"Успешно получена информация о странице {page_username}")
            
            return {
                "username": page_username,
                "name": profile.get("Name", ""),
                "about": profile.get("About", ""),
                "fan_count": profile.get("Likes", 0),
                "followers": profile.get("Followers", 0),
            }
        except ValueError as e:
            # Пробрасываем ValueError как есть
            logger.warning(f"Ошибка валидации при получении информации о странице: {e}")
            raise
        except Exception as e:
            logger.warning(f"Не удалось получить полную информацию о странице {page_username}: {e}", exc_info=True)
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Возвращаем базовую информацию вместо исключения
            return {
                "username": page_username,
                "name": page_username,
            }
    
    async def get_latest_post(self, page_username: str) -> Dict[str, Any]:
        """
        Получить последний пост со страницы
        
        Args:
            page_username: Username страницы
            
        Returns:
            Данные последнего поста
        """
        logger.info(f"Получаем последний пост для {page_username}")
        posts = await self._get_posts_async(page_username, pages=5)
        
        if not posts:
            logger.warning(f"Не найдено постов для {page_username}")
            return {}
        
        post = posts[0]
        logger.info(f"Обрабатываем первый пост: keys={list(post.keys())}")
        
        # Вспомогательная функция для конвертации даты в ISO формат
        def format_datetime(dt):
            """Конвертирует datetime объект в ISO строку или возвращает None"""
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.isoformat()
            if isinstance(dt, (int, float)):
                # Если это timestamp, конвертируем в datetime
                try:
                    return datetime.fromtimestamp(dt).isoformat()
                except (ValueError, OSError):
                    return None
            # Если это уже строка, возвращаем как есть
            return str(dt) if dt else None
        
        # Форматируем данные поста
        # facebook-scraper может использовать разные ключи в зависимости от версии
        formatted_post = {
            "post_id": post.get("post_id", post.get("post_url", "").split("/")[-1] if post.get("post_url") else ""),
            "text": post.get("text", post.get("post_text", "")),
            "time": format_datetime(post.get("time")),
            "timestamp": format_datetime(post.get("timestamp")),
            "post_url": post.get("post_url", ""),
            "likes": post.get("likes", 0),
            "comments": post.get("comments", 0),
            "shares": post.get("shares", 0),
            "reactions": post.get("reactions", {}),
            "images": post.get("images", []),
            "video": post.get("video", None),
        }
        
        return formatted_post
    
    async def get_post_reactions(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлечь реакции из данных поста
        
        Args:
            post_data: Данные поста от facebook-scraper
            
        Returns:
            Словарь с реакциями по типам
        """
        reactions = post_data.get("reactions", {})
        
        # facebook-scraper возвращает реакции в формате словаря
        # Например: {'👍': 100, '❤️': 50, '😮': 10, '😄': 5, '😢': 2, '😡': 1}
        
        # Маппинг эмодзи к типам реакций
        emoji_to_type = {
            '👍': 'LIKE',
            '❤️': 'LOVE',
            '😮': 'WOW',
            '😄': 'HAHA',
            '😢': 'SORRY',
            '😡': 'ANGER',
        }
        
        reactions_by_type = {}
        total_count = 0
        
        for emoji, count in reactions.items():
            reaction_type = emoji_to_type.get(emoji, emoji)
            reactions_by_type[reaction_type] = count
            total_count += count
        
        # Если реакции не найдены, используем общее количество лайков
        if not reactions_by_type and post_data.get("likes", 0) > 0:
            reactions_by_type["LIKE"] = post_data.get("likes", 0)
            total_count = post_data.get("likes", 0)
        
        return {
            "reactions_by_type": reactions_by_type,
            "total_reactions": total_count,
            "raw_reactions": reactions
        }
    
    async def get_post_comments(self, post_data: Dict[str, Any], limit: int = 100) -> Dict[str, Any]:
        """
        Извлечь комментарии из данных поста
        
        Args:
            post_data: Данные поста от facebook-scraper
            limit: Максимальное количество комментариев
            
        Returns:
            Список комментариев
        """
        comments_full = post_data.get("comments_full", [])
        
        # Вспомогательная функция для конвертации даты в ISO формат
        def format_datetime(dt):
            """Конвертирует datetime объект в ISO строку или возвращает None"""
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.isoformat()
            if isinstance(dt, (int, float)):
                # Если это timestamp, конвертируем в datetime
                try:
                    return datetime.fromtimestamp(dt).isoformat()
                except (ValueError, OSError):
                    return None
            # Если это уже строка, возвращаем как есть
            return str(dt) if dt else None
        
        formatted_comments = []
        
        for comment in comments_full[:limit]:
            formatted_comment = {
                "comment_id": comment.get("comment_id", ""),
                "text": comment.get("comment_text", ""),
                "author": comment.get("commenter_name", ""),
                "author_id": comment.get("commenter_id", ""),
                "time": format_datetime(comment.get("comment_time")),
                "likes": comment.get("comment_likes", 0),
                "replies": comment.get("replies", []),
            }
            formatted_comments.append(formatted_comment)
        
        return {
            "comments": formatted_comments,
            "total_count": len(formatted_comments)
        }
    
    def parse_comments_from_html(self, html_content: str, limit: int = 100) -> Dict[str, Any]:
        """
        Парсинг комментариев напрямую из HTML-структуры Facebook
        
        Args:
            html_content: HTML-строка с комментариями Facebook
            limit: Максимальное количество комментариев для извлечения
            
        Returns:
            Словарь с отформатированными комментариями
        """
        if BeautifulSoup is None:
            raise ImportError("BeautifulSoup не установлен. Установите: pip install beautifulsoup4")
        
        if not html_content or not html_content.strip():
            logger.warning("Получена пустая HTML-структура")
            return {
                "comments": [],
                "total_count": 0
            }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            comments = []
            
            # Различные селекторы для поиска комментариев в Facebook HTML
            # Facebook использует разные структуры, попробуем несколько вариантов
            
            # Вариант 1: Поиск по data-ft атрибутам (старая структура)
            comment_elements = soup.find_all(attrs={"data-ft": re.compile(r".*top_level_post_id.*")})
            
            # Вариант 2: Поиск по классам комментариев
            if not comment_elements:
                comment_elements = soup.find_all('div', class_=re.compile(r'.*comment.*', re.I))
            
            # Вариант 3: Поиск по структуре с userContentWrapper
            if not comment_elements:
                comment_elements = soup.find_all('div', attrs={"data-testid": re.compile(r".*comment.*", re.I)})
            
            # Вариант 4: Поиск по структуре с role="article" (часто используется для комментариев)
            if not comment_elements:
                comment_elements = soup.find_all('div', role="article")
            
            # Вариант 5: Поиск по структуре с data-sigil (используется в мобильной версии)
            if not comment_elements:
                comment_elements = soup.find_all(attrs={"data-sigil": re.compile(r".*comment.*", re.I)})
            
            logger.info(f"Найдено {len(comment_elements)} потенциальных элементов комментариев")
            
            for idx, element in enumerate(comment_elements[:limit]):
                try:
                    comment_data = self._extract_comment_data(element)
                    if comment_data and comment_data.get("text"):
                        comments.append(comment_data)
                except Exception as e:
                    logger.debug(f"Ошибка при извлечении комментария #{idx}: {e}")
                    continue
            
            logger.info(f"Успешно извлечено {len(comments)} комментариев из HTML")
            
            return {
                "comments": comments,
                "total_count": len(comments)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге HTML комментариев: {e}", exc_info=True)
            return {
                "comments": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def _extract_comment_data(self, element) -> Optional[Dict[str, Any]]:
        """
        Извлечь данные одного комментария из HTML-элемента
        
        Args:
            element: BeautifulSoup элемент с комментарием
            
        Returns:
            Словарь с данными комментария или None
        """
        try:
            comment_data = {}
            
            # Извлечение текста комментария
            # Пробуем разные селекторы для текста
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
            
            # Если не нашли через селекторы, пробуем найти любой текст внутри
            if not text:
                # Ищем все текстовые узлы, но пропускаем ссылки и кнопки
                text_parts = []
                for text_node in element.find_all(string=True):
                    parent = text_node.parent
                    if parent and parent.name not in ['a', 'button', 'script', 'style']:
                        text_part = text_node.strip()
                        if text_part:
                            text_parts.append(text_part)
                text = ' '.join(text_parts).strip()
            
            comment_data["text"] = text or ""
            
            # Извлечение имени автора
            author_selectors = [
                'a[role="link"]',
                'strong a',
                'h3 a',
                '[data-hovercard-prefer-more-content-show="1"]',
                'a[href*="/user/"]',
                'a[href*="/profile.php"]',
            ]
            
            author = None
            author_id = None
            for selector in author_selectors:
                author_elem = element.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    href = author_elem.get('href', '')
                    # Извлекаем ID из ссылки
                    if '/user/' in href:
                        author_id = href.split('/user/')[-1].split('/')[0].split('?')[0]
                    elif 'profile.php?id=' in href:
                        author_id = href.split('profile.php?id=')[-1].split('&')[0]
                    if author:
                        break
            
            comment_data["author"] = author or ""
            comment_data["author_id"] = author_id or ""
            
            # Извлечение времени комментария
            time_selectors = [
                'a[href*="/comment/"]',
                'a abbr',
                '[data-tooltip-content]',
                'a[title]',
            ]
            
            time_str = None
            for selector in time_selectors:
                time_elem = element.select_one(selector)
                if time_elem:
                    time_str = time_elem.get('title') or time_elem.get('data-tooltip-content') or time_elem.get_text(strip=True)
                    if time_str:
                        break
            
            comment_data["time"] = time_str or ""
            
            # Извлечение количества лайков
            likes_selectors = [
                '[aria-label*="Like"]',
                '[data-sigil="reactions-count"]',
                '.like-count',
            ]
            
            likes = 0
            for selector in likes_selectors:
                likes_elem = element.select_one(selector)
                if likes_elem:
                    likes_text = likes_elem.get_text(strip=True)
                    # Пытаемся извлечь число из текста
                    likes_match = re.search(r'(\d+)', likes_text.replace(',', '').replace('.', ''))
                    if likes_match:
                        try:
                            likes = int(likes_match.group(1))
                            break
                        except ValueError:
                            pass
            
            comment_data["likes"] = likes
            
            # Извлечение ID комментария
            comment_id = element.get('id') or element.get('data-ft', '')
            if comment_id and isinstance(comment_id, str):
                # Пытаемся извлечь ID из data-ft JSON
                if 'top_level_post_id' in comment_id:
                    try:
                        import json
                        # data-ft может быть JSON строкой
                        ft_data = json.loads(comment_id) if comment_id.startswith('{') else {}
                        comment_id = ft_data.get('top_level_post_id', '')
                    except:
                        # Если не JSON, пытаемся извлечь через regex
                        id_match = re.search(r'top_level_post_id["\']?\s*:\s*["\']?(\d+)', comment_id)
                        if id_match:
                            comment_id = id_match.group(1)
            
            comment_data["comment_id"] = str(comment_id) if comment_id else ""
            
            # Извлечение ответов (replies) - упрощенная версия
            replies = []
            reply_elements = element.find_all('div', class_=re.compile(r'.*reply.*', re.I))
            for reply_elem in reply_elements[:5]:  # Ограничиваем количество ответов
                reply_data = self._extract_comment_data(reply_elem)
                if reply_data:
                    replies.append(reply_data)
            
            comment_data["replies"] = replies
            
            return comment_data
            
        except Exception as e:
            logger.debug(f"Ошибка при извлечении данных комментария: {e}")
            return None
    
    async def get_page_post_data(self, page_username: str) -> Dict[str, Any]:
        """
        Получить полные данные последнего поста страницы (УПРОЩЕННАЯ ВЕРСИЯ для отладки):
        - Информацию о посте (БЕЗ реакций и комментариев для начала)
        
        Args:
            page_username: Username страницы (например, 'premierbankso')
            
        Returns:
            Полные данные поста
        """
        try:
            logger.info(f"=== Начало получения данных для {page_username} ===")
            
            # ШАГ 1: Получаем информацию о странице (может не работать без cookies)
            try:
                page_info = await self.get_page_info(page_username)
                logger.info(f"✅ Информация о странице получена: {page_info}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить информацию о странице: {e}")
                page_info = {
                    "username": page_username,
                    "name": page_username,
                }
            
            # ШАГ 2: Получаем последний пост (ГЛАВНОЕ)
            logger.info(f"Получаем последний пост...")
            latest_post = await self.get_latest_post(page_username)
            
            if not latest_post:
                logger.warning(f"Посты не найдены для {page_username}")
                return {
                    "page_info": page_info,
                    "error": "На странице нет постов или страница недоступна",
                    "fetched_at": datetime.now().isoformat()
                }
            
            logger.info(f"✅ Пост получен: post_id={latest_post.get('post_id', 'N/A')}")
            
            # УПРОЩЕННАЯ ВЕРСИЯ - БЕЗ реакций и комментариев для отладки
            # reactions = await self.get_post_reactions(latest_post)
            # comments = await self.get_post_comments(latest_post)
            
            return {
                "page_info": page_info,
                "post": latest_post,
                "reactions": {"total_reactions": 0, "reactions_by_type": {}},  # Заглушка
                "comments": {"comments": [], "total_count": 0},  # Заглушка
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных: {type(e).__name__}: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise ValueError(f"Не удалось получить данные со страницы {page_username}: {str(e)}")
    
    def _load_cookies_dict(self) -> Dict[str, str]:
        """
        Загрузить cookies из файла в словарь для httpx
        
        Returns:
            Словарь с cookies в формате {name: value}
        """
        cookies_dict = {}
        
        if not self.cookies:
            return cookies_dict
        
        try:
            with open(self.cookies, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Пропускаем комментарии и пустые строки
                    if not line or line.startswith('#'):
                        continue
                    
                    # Формат Netscape HTTP Cookie File:
                    # domain	flag	path	secure	expiration	name	value
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        cookie_name = parts[5]
                        cookie_value = parts[6] if len(parts) > 6 else ''
                        cookies_dict[cookie_name] = cookie_value
        except Exception as e:
            logger.warning(f"Не удалось загрузить cookies из файла {self.cookies}: {e}")
        
        return cookies_dict
    
    async def fetch_and_parse_comments_from_url(self, url: str, limit: int = 100) -> Dict[str, Any]:
        """
        Загрузить HTML со страницы Facebook и распарсить комментарии
        
        Args:
            url: URL страницы Facebook с комментариями
            limit: Максимальное количество комментариев для извлечения
            
        Returns:
            Словарь с отформатированными комментариями и метаданными
        """
        if httpx is None:
            raise ImportError("httpx не установлен. Установите: pip install httpx")
        
        try:
            logger.info(f"Загружаем HTML со страницы: {url}")
            
            # Загружаем cookies если есть
            cookies_dict = self._load_cookies_dict()
            
            # Заголовки для запроса
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            # Загружаем HTML
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers, cookies=cookies_dict)
                response.raise_for_status()
                
                html_content = response.text
                logger.info(f"HTML загружен, размер: {len(html_content)} символов")
            
            # Парсим комментарии из HTML
            result = self.parse_comments_from_html(html_content, limit=limit)
            
            # Добавляем метаданные
            result["url"] = url
            result["fetched_at"] = datetime.now().isoformat()
            result["html_size"] = len(html_content)
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при загрузке страницы {url}: {e.response.status_code}")
            raise ValueError(f"Не удалось загрузить страницу: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к {url}: {e}")
            raise ValueError(f"Ошибка соединения: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке и парсинге комментариев: {e}", exc_info=True)
            raise ValueError(f"Ошибка при обработке страницы: {str(e)}")
    
    def _load_cookies_for_playwright(self) -> List[Dict[str, Any]]:
        """
        Загрузить cookies из файла в формате для Playwright
        
        Returns:
            Список словарей с cookies для Playwright
        """
        playwright_cookies = []
        
        if not self.cookies:
            return playwright_cookies
        
        try:
            with open(self.cookies, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain = parts[0].lstrip('.')
                        path = parts[2]
                        secure = parts[3] == 'TRUE'
                        expiration = int(parts[4]) if parts[4] != '0' else None
                        name = parts[5]
                        value = parts[6] if len(parts) > 6 else ''
                        
                        cookie = {
                            "name": name,
                            "value": value,
                            "domain": domain,
                            "path": path,
                            "secure": secure,
                        }
                        
                        if expiration:
                            cookie["expires"] = expiration
                        
                        playwright_cookies.append(cookie)
        except Exception as e:
            logger.warning(f"Не удалось загрузить cookies для Playwright: {e}")
        
        return playwright_cookies
    
    async def fetch_and_parse_comments_with_browser(self, url: str, limit: int = 100, wait_time: int = 5) -> Dict[str, Any]:
        """
        Загрузить страницу через браузер (Playwright) с рендерингом JavaScript и распарсить комментарии
        
        Этот метод использует реальный браузер для рендеринга JavaScript, что позволяет
        извлекать комментарии, которые загружаются динамически.
        
        Args:
            url: URL страницы Facebook с комментариями
            limit: Максимальное количество комментариев для извлечения
            wait_time: Время ожидания загрузки страницы в секундах (по умолчанию 5)
            
        Returns:
            Словарь с отформатированными комментариями и метаданными, включая статус выполнения
        """
        if async_playwright is None:
            raise ImportError(
                "Playwright не установлен. Установите: pip install playwright && playwright install chromium"
            )
        
        start_time = datetime.now()
        status = "started"
        
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 НАЧАЛО СКРАПИНГА: {url}")
            logger.info(f"⏰ Время начала: {start_time.isoformat()}")
            logger.info("=" * 80)
            
            status = "initializing_browser"
            logger.info("📦 Этап 1/5: Инициализация браузера...")
            
            # Пробуем мобильную версию (часто более доступна)
            mobile_url = url.replace("www.facebook.com", "m.facebook.com")
            
            async with async_playwright() as p:
                # Запускаем браузер
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080}
                )
                
                # Загружаем cookies если есть
                playwright_cookies = self._load_cookies_for_playwright()
                if playwright_cookies:
                    await context.add_cookies(playwright_cookies)
                    logger.info(f"✅ Загружено {len(playwright_cookies)} cookies")
                else:
                    logger.warning("⚠️  Cookies не найдены")
                
                page = await context.new_page()
                
                try:
                    status = "loading_page"
                    logger.info("📥 Этап 2/5: Загрузка страницы...")
                    logger.info(f"   URL: {mobile_url}")
                    
                    await page.goto(mobile_url, wait_until="networkidle", timeout=30000)
                    logger.info("✅ Страница загружена")
                    
                    status = "waiting_comments"
                    logger.info(f"⏳ Этап 3/5: Ожидание загрузки комментариев ({wait_time} секунд)...")
                    await page.wait_for_timeout(wait_time * 1000)
                    
                    status = "scrolling"
                    logger.info("📜 Этап 4/5: Прокрутка страницы для загрузки комментариев...")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    logger.info("✅ Прокрутка завершена")
                    
                    status = "extracting_html"
                    logger.info("🔍 Этап 5/5: Извлечение HTML...")
                    html_content = await page.content()
                    logger.info(f"✅ HTML извлечен, размер: {len(html_content):,} символов")
                    
                finally:
                    await page.close()
                    await context.close()
                    await browser.close()
                    logger.info("🔒 Браузер закрыт")
            
            status = "parsing_comments"
            logger.info("🔧 Парсинг комментариев из HTML...")
            result = self.parse_comments_from_html(html_content, limit=limit)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            comments_count = result.get('total_count', 0)
            comments = result.get('comments', [])
            status = "completed" if comments_count > 0 else "completed_no_comments"
            
            # Выводим комментарии в логи
            if comments:
                logger.info("")
                logger.info("💬 ИЗВЛЕЧЕННЫЕ КОММЕНТАРИИ:")
                logger.info("-" * 80)
                for i, comment in enumerate(comments, 1):
                    author = comment.get('author', 'Аноним') or 'Аноним'
                    text = comment.get('text', '') or ''
                    likes = comment.get('likes', 0)
                    time_str = comment.get('time', '') or ''
                    comment_id = comment.get('comment_id', '') or ''
                    
                    logger.info(f"\n📝 Комментарий #{i}:")
                    logger.info(f"   👤 Автор: {author}")
                    if text:
                        # Выводим полный текст комментария
                        logger.info(f"   💭 Текст: {text}")
                    if likes > 0:
                        logger.info(f"   ❤️  Лайков: {likes}")
                    if time_str:
                        logger.info(f"   🕐 Время: {time_str}")
                    if comment_id:
                        logger.info(f"   🆔 ID: {comment_id}")
                    logger.info("-" * 80)
            
            # Добавляем метаданные и статус
            result["url"] = url
            result["fetched_at"] = end_time.isoformat()
            result["started_at"] = start_time.isoformat()
            result["duration_seconds"] = round(duration, 2)
            result["html_size"] = len(html_content)
            result["method"] = "browser_rendering"
            result["status"] = status
            result["success"] = True
            
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"✅ СКРАПИНГ ЗАВЕРШЕН УСПЕШНО")
            logger.info(f"   Статус: {status}")
            logger.info(f"   Найдено комментариев: {comments_count}")
            logger.info(f"   Время выполнения: {duration:.2f} секунд")
            logger.info(f"   Время завершения: {end_time.isoformat()}")
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            status = "failed"
            
            logger.error("=" * 80)
            logger.error(f"❌ СКРАПИНГ ЗАВЕРШЕН С ОШИБКОЙ")
            logger.error(f"   Статус: {status}")
            logger.error(f"   Ошибка: {str(e)}")
            logger.error(f"   Время выполнения до ошибки: {duration:.2f} секунд")
            logger.error("=" * 80)
            
            # Возвращаем результат с ошибкой
            return {
                "url": url,
                "status": status,
                "success": False,
                "error": str(e),
                "started_at": start_time.isoformat(),
                "fetched_at": end_time.isoformat(),
                "duration_seconds": round(duration, 2),
                "comments": [],
                "total_count": 0
            }

