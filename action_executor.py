#!/usr/bin/env python
import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from typing import Optional

class ActionExecutor:
    """
    Исполняет действия с браузером (Playwright). 
    Обеспечивает асинхронную инициализацию и корректное закрытие ресурсов.
    """
    def __init__(self, headless: bool = True):
        # Убедимся, что headless всегда булево значение
        self.headless_mode: bool = bool(headless)
        self.playwright: Optional[async_playwright] = None
        self.browser: Optional[object] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def setup(self) -> None:
        """Асинхронная инициализация всех ресурсов (Playwright, Browser)."""
        if self.playwright is not None: return # Already set up
        print("[ACTION_EXECUTOR] Инициализация Playwright и браузера...")
        try:
            self.playwright = await async_playwright().start()
            # Используем 'async with' или явное управление для ресурсов
            self.browser = await self.playwright.chromium.launch(headless=self.headless_mode)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            print("[ACTION_EXECUTOR] Успешно инициализирован браузер и страница.")
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Критическая ошибка при настройке: {e}")
            raise RuntimeError("Не удалось настроить исполнитель действий (ActionExecutor).") from e

    async def execute_action(self, url: str) -> str:
        """Выполняет навигацию и возвращает результат."""
        if not self.page: 
            raise RuntimeError("ActionExecutor не инициализирован. Вызовите setup() первым.")
        
        print(f"[ACTION_EXECUTOR] Переход на URL: {url}")
        await self.page.goto(url, wait_until='domcontentloaded')
        # Простой способ получить контент для отчета об успехе
        content = await self.page.inner_html()
        return f"Успешно загружено. Начало содержимого: {content[:200]}..."

    async def close(self) -> None:
        """Гарантированное закрытие всех ресурсов (Browser, Playwright)."""
        print("[ACTION_EXECUTOR] Запуск процедуры очистки ресурсов.")
        if self.page: await self.page.close()
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        print("[ACTION_EXECUTOR] Ресурсы успешно освобождены.")

    # Контекстный менеджер для лучшей интеграции (опционально, но рекомендуется)
    async def __aenter__(self): 
        await self.setup() 
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: 
        await self.close()
