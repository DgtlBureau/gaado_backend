"""
Пример интеграции Playwright Worker в основной API

Этот файл показывает, как модифицировать facebook_client.py
для использования внешнего Playwright Worker сервиса
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# URL Playwright Worker сервиса
PLAYWRIGHT_SERVICE_URL = os.getenv("PLAYWRIGHT_SERVICE_URL", "http://localhost:8001")
USE_EXTERNAL_PLAYWRIGHT = os.getenv("USE_EXTERNAL_PLAYWRIGHT", "true").lower() == "true"


async def fetch_with_external_playwright(
    url: str,
    wait_time: int = 5,
    cookies: Optional[list] = None,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Использовать внешний Playwright Worker для скраппинга
    
    Args:
        url: URL для скраппинга
        wait_time: Время ожидания в секундах
        cookies: Список cookies для браузера
        timeout: Таймаут запроса в секундах
        
    Returns:
        Словарь с HTML и метаданными
    """
    if not USE_EXTERNAL_PLAYWRIGHT:
        raise ValueError("USE_EXTERNAL_PLAYWRIGHT отключен")
    
    logger.info(f"Используем внешний Playwright Worker: {PLAYWRIGHT_SERVICE_URL}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Проверяем доступность сервиса
            try:
                health_response = await client.get(f"{PLAYWRIGHT_SERVICE_URL}/health")
                if health_response.status_code != 200:
                    raise ConnectionError(f"Playwright Worker недоступен: {health_response.status_code}")
            except httpx.RequestError as e:
                raise ConnectionError(f"Не удалось подключиться к Playwright Worker: {e}")
            
            # Отправляем запрос на скраппинг
            request_data = {
                "url": url,
                "wait_time": wait_time,
                "scroll": True
            }
            
            if cookies:
                request_data["cookies"] = cookies
            
            logger.info(f"Отправляем запрос на скраппинг: {url}")
            response = await client.post(
                f"{PLAYWRIGHT_SERVICE_URL}/scrape",
                json=request_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Скраппинг завершен: {result.get('html_size', 0)} символов")
            
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP ошибка от Playwright Worker: {e.response.status_code}")
        error_detail = e.response.json().get("detail", str(e)) if e.response.text else str(e)
        raise ValueError(f"Ошибка Playwright Worker: {error_detail}")
    
    except httpx.TimeoutException:
        logger.error(f"Таймаут при запросе к Playwright Worker")
        raise ValueError("Таймаут при скраппинге через Playwright Worker")
    
    except Exception as e:
        logger.error(f"Ошибка при использовании Playwright Worker: {e}", exc_info=True)
        raise ValueError(f"Ошибка Playwright Worker: {str(e)}")


# Пример модификации метода в FacebookScraperClient
"""
В facebook_client.py замените метод fetch_and_parse_comments_with_browser:

async def fetch_and_parse_comments_with_browser(self, url: str, limit: int = 100, wait_time: int = 5) -> Dict[str, Any]:
    \"\"\"
    Загрузить страницу через браузер (Playwright) с рендерингом JavaScript
    
    Использует внешний Playwright Worker сервис если USE_EXTERNAL_PLAYWRIGHT=True,
    иначе использует локальный Playwright (только для разработки).
    \"\"\"
    # Проверяем, используем ли внешний сервис
    if USE_EXTERNAL_PLAYWRIGHT:
        logger.info("Используем внешний Playwright Worker")
        
        # Загружаем cookies для Playwright Worker
        playwright_cookies = self._load_cookies_for_playwright()
        
        # Вызываем внешний сервис
        result = await fetch_with_external_playwright(
            url=url,
            wait_time=wait_time,
            cookies=playwright_cookies
        )
        
        # Парсим комментарии из полученного HTML
        html_content = result.get("html", "")
        parsed_result = self.parse_comments_from_html(html_content, limit=limit)
        
        # Объединяем результаты
        return {
            **parsed_result,
            "url": url,
            "fetched_at": result.get("fetched_at"),
            "duration_seconds": result.get("duration_seconds"),
            "html_size": result.get("html_size"),
            "method": "external_browser_worker",
            "status": "completed",
            "success": True
        }
    
    # Локальный Playwright (только для разработки)
    # ... существующий код ...
"""

