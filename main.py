#!/usr/bin/env python
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
# Импортируем наши собственные модули!
from memory_manager import MemoryManager
from action_executor import ActionExecutor

async def main():
    """
    Главная точка входа (entry point) для Агента RPA. 
    Оркеструет работу памяти и действий.
    """
    print("===============================================")
    print("🤖 АВТОНОМНЫЙ АГЕНТ: ЗАПУСК СИСТЕМЫ")
    print("===============================================")

    try:
        # 1. Инициализация Памяти
        memory_manager = MemoryManager()
        print(f"[CORE] Статус памяти загружен: {memory_manager.current_status}")
        
        # 2. Инициализация Действий (ActionExecutor)
        action_executor = ActionExecutor()

        async with async_playwright() as p:
            # Запуск браузера с фокусом на отладке (headless=False)
            await action_executor.setup_browser("http://localhost") 
            print("[CORE] Браузер запущен и готов к работе.")

            # Получаем текущий контекст из памяти, чтобы понять, что делать дальше
            initial_context = memory_manager.get_context('last_known_url')
            if not initial_context:
                # Если нет сохраненного URL, используем базовый.
                target_url = "http://localhost" 
                await action_executor.page.goto(target_url)
                memory_manager.save_memory("last_known_url", target_url)
            else:
                 # Пытаемся вернуться к последнему известному URL, если это возможно
                 print(f"[CORE] Попытка продолжить работу с последнего места: {initial_context}")

            await action_executor.take_screenshot("startup_success.png") # Снимок при старте
            memory_manager.save_memory("last_activity", "Startup successful.")


            # --- 3. АВТОНОМНЫЙ ЦИКЛ РАБОТЫ (Ядро Агента) ---
            print("\n--- [CORE] ВХОД В ПРОАКТИВНЫЙ ЦИКЛ ---\n")
            
            # Здесь должна быть сложная логика принятия решений:
            # 1. Проверить MemoryManager для директивы (task_directive).
            # 2. Если есть, вызвать соответствующий метод в ActionExecutor.
            # 3. Иначе - выполнить рутинную проверку и сохранить статус.

            print("[CORE] Агент ждет директиву или выполняет стандартный мониторинг.")
            await asyncio.sleep(10) # Пауза для имитации "ожидания"
            
            # --- Симуляция действия после ожидания (Демонстрация использования ActionExecutor)---
            print("\n[CORE] Выполняем симулированный клик по координатам 500, 300.")
            await action_executor.click_at_coordinates(500, 300)

            # Сохранение окончательного результата и статуса сессии
            memory_manager.save_memory("session_status", "Completed cycle successfully")
            print("\n[CORE] Цикл завершен. Состояние сохранено.")


    except PlaywrightTimeoutError:
        print("[CRITICAL FAIL] Сбой из-за таймаута элемента. Проверьте селекторы и доступность элементов на странице.")
    except Exception as e:
        print(f"\n[FATAL ERROR] Непредвиденная критическая ошибка агента: {e}")
        # Критически важно! Снимок при любой ошибке
        await action_executor.take_screenshot("error_capture.png") 
    finally:
        # Гарантированное закрытие ресурсов в любом случае (Успех, Ошибка, Прерывание)
        print("\n[CLEANUP] Закрытие всех браузерных сессий...")
        await action_executor.close()
        print("===============================================")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[EXIT] Агент вручную остановлен пользователем.")

