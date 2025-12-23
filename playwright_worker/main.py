"""
Playwright Worker Service
Отдельный FastAPI сервис для выполнения браузерной автоматизации
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    logger.error("Playwright не установлен. Установите: pip install playwright && playwright install chromium")
    async_playwright = None

app = FastAPI(
    title="Playwright Worker Service",
    description="Сервис для браузерной автоматизации и скраппинга",
    version="1.0.0"
)

# Ограничения для безопасности
MAX_CONCURRENT_BROWSERS = int(os.getenv("MAX_CONCURRENT_BROWSERS", "5"))
MAX_WAIT_TIME = int(os.getenv("MAX_WAIT_TIME", "30"))
ALLOWED_DOMAINS = os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else None

# Счетчик активных браузеров
active_browsers = 0
browser_lock = asyncio.Lock()


class ScrapeRequest(BaseModel):
    """Запрос на скраппинг страницы"""
    url: str = Field(..., description="URL страницы для скраппинга")
    wait_time: Optional[int] = Field(default=5, ge=1, le=MAX_WAIT_TIME, description="Время ожидания в секундах")
    scroll: Optional[bool] = Field(default=True, description="Прокручивать страницу для загрузки контента")
    cookies: Optional[List[Dict[str, Any]]] = Field(default=None, description="Cookies для браузера")
    user_agent: Optional[str] = Field(default=None, description="User-Agent для браузера")


class ScreenshotRequest(BaseModel):
    """Запрос на скриншот страницы"""
    url: str = Field(..., description="URL страницы для скриншота")
    wait_time: Optional[int] = Field(default=5, ge=1, le=MAX_WAIT_TIME)
    full_page: Optional[bool] = Field(default=False, description="Скриншот всей страницы")
    width: Optional[int] = Field(default=1920, description="Ширина viewport")
    height: Optional[int] = Field(default=1080, description="Высота viewport")


def check_domain_allowed(url: str) -> bool:
    """Проверка, разрешен ли домен для скраппинга"""
    if ALLOWED_DOMAINS is None:
        return True
    
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return any(allowed in domain for allowed in ALLOWED_DOMAINS if allowed)


async def acquire_browser():
    """Получить разрешение на запуск браузера"""
    global active_browsers
    
    async with browser_lock:
        if active_browsers >= MAX_CONCURRENT_BROWSERS:
            raise HTTPException(
                status_code=503,
                detail=f"Достигнут лимит одновременных браузеров ({MAX_CONCURRENT_BROWSERS}). Попробуйте позже."
            )
        active_browsers += 1
        logger.info(f"Запущен браузер. Активных: {active_browsers}/{MAX_CONCURRENT_BROWSERS}")


async def release_browser():
    """Освободить слот браузера"""
    global active_browsers
    
    async with browser_lock:
        active_browsers = max(0, active_browsers - 1)
        logger.info(f"Браузер закрыт. Активных: {active_browsers}/{MAX_CONCURRENT_BROWSERS}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    playwright_available = async_playwright is not None
    
    return {
        "status": "healthy" if playwright_available else "degraded",
        "playwright_available": playwright_available,
        "active_browsers": active_browsers,
        "max_concurrent_browsers": MAX_CONCURRENT_BROWSERS,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scrape")
async def scrape_page(request: ScrapeRequest):
    """
    Скраппинг страницы через браузер с рендерингом JavaScript
    
    Args:
        request: Параметры скраппинга
        
    Returns:
        HTML контент страницы и метаданные
    """
    if async_playwright is None:
        raise HTTPException(
            status_code=500,
            detail="Playwright не установлен. Установите: pip install playwright && playwright install chromium"
        )
    
    # Проверка домена
    if not check_domain_allowed(request.url):
        raise HTTPException(
            status_code=403,
            detail=f"Домен {request.url} не разрешен для скраппинга"
        )
    
    start_time = datetime.now()
    browser = None
    
    try:
        # Получаем разрешение на запуск браузера
        await acquire_browser()
        
        logger.info(f"Начинаем скраппинг: {request.url}")
        
        async with async_playwright() as p:
            # Запускаем браузер
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']  # Для Docker/серверов
            )
            
            # Создаем контекст браузера
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": request.user_agent or (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            
            context = await browser.new_context(**context_options)
            
            # Загружаем cookies если есть
            if request.cookies:
                await context.add_cookies(request.cookies)
                logger.info(f"Загружено {len(request.cookies)} cookies")
            
            page = await context.new_page()
            
            try:
                # Загружаем страницу
                logger.info(f"Загружаем страницу: {request.url}")
                await page.goto(request.url, wait_until="networkidle", timeout=30000)
                
                # Ждем загрузки контента
                logger.info(f"Ожидание {request.wait_time} секунд...")
                await page.wait_for_timeout(request.wait_time * 1000)
                
                # Прокручиваем страницу если нужно
                if request.scroll:
                    logger.info("Прокрутка страницы...")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                
                # Получаем HTML
                html_content = await page.content()
                logger.info(f"HTML получен, размер: {len(html_content):,} символов")
                
            finally:
                await page.close()
                await context.close()
                await browser.close()
                browser = None
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "success": True,
            "url": request.url,
            "html": html_content,
            "html_size": len(html_content),
            "duration_seconds": round(duration, 2),
            "fetched_at": end_time.isoformat(),
            "method": "browser_rendering"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при скраппинге {request.url}: {e}", exc_info=True)
        
        # Закрываем браузер если он еще открыт
        if browser:
            try:
                await browser.close()
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при скраппинге: {str(e)}"
        )
    
    finally:
        # Освобождаем слот браузера
        await release_browser()


@app.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest):
    """
    Сделать скриншот страницы
    
    Args:
        request: Параметры скриншота
        
    Returns:
        Base64 encoded изображение
    """
    if async_playwright is None:
        raise HTTPException(
            status_code=500,
            detail="Playwright не установлен"
        )
    
    if not check_domain_allowed(request.url):
        raise HTTPException(
            status_code=403,
            detail=f"Домен {request.url} не разрешен"
        )
    
    browser = None
    
    try:
        await acquire_browser()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": request.width, "height": request.height}
            )
            page = await context.new_page()
            
            try:
                await page.goto(request.url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(request.wait_time * 1000)
                
                screenshot_bytes = await page.screenshot(
                    full_page=request.full_page,
                    type="png"
                )
                
                import base64
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                return {
                    "success": True,
                    "url": request.url,
                    "screenshot": screenshot_base64,
                    "format": "png",
                    "full_page": request.full_page,
                    "fetched_at": datetime.now().isoformat()
                }
                
            finally:
                await page.close()
                await context.close()
                await browser.close()
                browser = None
    
    except Exception as e:
        logger.error(f"Ошибка при создании скриншота: {e}", exc_info=True)
        if browser:
            try:
                await browser.close()
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        await release_browser()


@app.get("/stats")
async def get_stats():
    """Получить статистику сервиса"""
    return {
        "active_browsers": active_browsers,
        "max_concurrent_browsers": MAX_CONCURRENT_BROWSERS,
        "max_wait_time": MAX_WAIT_TIME,
        "allowed_domains": ALLOWED_DOMAINS,
        "playwright_available": async_playwright is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

