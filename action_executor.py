#!/usr/bin/env python
import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from typing import Optional, Tuple


class ActionExecutor:
    """
    Исполняет действия с браузером (Playwright).
    Обеспечивает асинхронную инициализацию и корректное закрытие ресурсов.
    Поддерживает работу с координатами, скриншотами и различными действиями.
    """
    
    def __init__(self, headless: bool = False):
        # headless=False по умолчанию для визуального наблюдения
        self.headless_mode: bool = bool(headless)
        self.playwright = None
        self.browser: Optional[object] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._viewport_width = 1920
        self._viewport_height = 1080

    async def setup(self) -> None:
        """Асинхронная инициализация всех ресурсов (Playwright, Browser)."""
        if self.playwright is not None:
            return  # Already set up
        
        print("[ACTION_EXECUTOR] Инициализация Playwright и браузера...")
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless_mode,
                args=[f'--window-size={self._viewport_width},{self._viewport_height}']
            )
            self.context = await self.browser.new_context(
                viewport={"width": self._viewport_width, "height": self._viewport_height}
            )
            self.page = await self.context.new_page()
            print(f"[ACTION_EXECUTOR] Браузер инициализирован с viewport {self._viewport_width}x{self._viewport_height}")
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Критическая ошибка при настройке: {e}")
            raise RuntimeError("Не удалось настроить исполнитель действий (ActionExecutor).") from e

    async def navigate_to(self, url: str) -> bool:
        """Переходит на указанный URL."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован. Вызовите setup() первым.")
        
        print(f"[ACTION_EXECUTOR] Переход на URL: {url}")
        try:
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            return True
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка навигации: {e}")
            return False

    async def click_at_coordinates(self, x: int, y: int, button: str = "left") -> bool:
        """Клик в указанные координаты."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        print(f"[ACTION_EXECUTOR] Клик в координаты ({x}, {y}), кнопка: {button}")
        try:
            await self.page.mouse.click(x, y, button=button)
            return True
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка клика: {e}")
            return False

    async def type_text(self, text: str, clear_first: bool = False) -> bool:
        """Ввод текста в текущее поле."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        print(f"[ACTION_EXECUTOR] Ввод текста: {text[:50]}..." if len(text) > 50 else f"[ACTION_EXECUTOR] Ввод текста: {text}")
        try:
            if clear_first:
                await self.page.keyboard.press("Control+a")
                await self.page.keyboard.press("Delete")
            await self.page.keyboard.type(text)
            return True
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка ввода текста: {e}")
            return False

    async def press_key(self, key: str) -> bool:
        """Нажатие клавиши или комбинации."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        print(f"[ACTION_EXECUTOR] Нажатие клавиши: {key}")
        try:
            await self.page.keyboard.press(key)
            return True
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка нажатия клавиши: {e}")
            return False

    async def scroll_page(self, direction: str, amount: int = 300) -> bool:
        """Прокрутка страницы."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        print(f"[ACTION_EXECUTOR] Прокрутка {direction} на {amount} пикселей")
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            return True
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка прокрутки: {e}")
            return False

    async def take_screenshot(self, filepath: str = "screenshot.png") -> str:
        """Делает скриншот текущей страницы."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        print(f"[ACTION_EXECUTOR] Скриншот: {filepath}")
        try:
            await self.page.screenshot(path=filepath, full_page=False)
            return filepath
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка скриншота: {e}")
            return ""

    async def get_page_content(self) -> str:
        """Получает HTML содержимое страницы."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        try:
            return await self.page.content()
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка получения контента: {e}")
            return ""

    async def get_page_url(self) -> str:
        """Получает текущий URL страницы."""
        if not self.page:
            raise RuntimeError("ActionExecutor не инициализирован.")
        
        return self.page.url

    async def close(self) -> None:
        """Гарантированное закрытие всех ресурсов."""
        print("[ACTION_EXECUTOR] Запуск процедуры очистки ресурсов.")
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("[ACTION_EXECUTOR] Ресурсы успешно освобождены.")
        except Exception as e:
            print(f"[ACTION_EXECUTOR ERROR] Ошибка при очистке: {e}")

    # Контекстный менеджер
    async def __aenter__(self):
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
