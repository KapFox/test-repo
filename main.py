#!/usr/bin/env python
"""
Autonomous RPA Agent - Главная точка входа
Автономный агент с LLM-оркестрацией, анализом экрана и циклами сна
"""
import asyncio
import os
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright
from memory_manager import MemoryManager
from action_executor import ActionExecutor
from llm_orchestrator import LLMOrchestrator


class AutonomousAgent:
    """
    Автономный RPA-агент с искусственным интеллектом.
    Анализирует экран через скриншоты, принимает решения через LLM,
    использует память для хранения контекста и обучения.
    """
    
    def __init__(self, headless: bool = False, sleep_cycle_hours: int = 6):
        self.headless = headless
        self.sleep_cycle_hours = sleep_cycle_hours
        self.memory_manager = MemoryManager()
        self.action_executor = ActionExecutor(headless=headless)
        self.llm_orchestrator = LLMOrchestrator()
        
        self.task_context = ""
        self.running = True
        self.screenshot_counter = 0
        
    async def initialize(self) -> None:
        """Инициализация всех компонентов агента."""
        print("=" * 60)
        print("🤖 АВТОНОМНЫЙ RPA-АГЕНТ: ЗАПУСК СИСТЕМЫ")
        print("=" * 60)
        
        # Инициализация браузера
        await self.action_executor.setup()
        print("[AGENT] Браузер запущен и готов к работе.")
        
        # Загрузка последнего состояния
        last_url = self.memory_manager.get_context('last_known_url')
        if last_url:
            print(f"[AGENT] Восстановление сессии: {last_url}")
            await self.action_executor.navigate_to(last_url)
        else:
            # Стартовая страница
            start_url = os.getenv("START_URL", "https://www.google.com")
            await self.action_executor.navigate_to(start_url)
            self.memory_manager.save_memory(
                "last_known_url", start_url,
                category="context", priority="medium"
            )
        
        # Начальный скриншот
        await self._take_screenshot("startup")
        
        print(f"[AGENT] Статистика памяти: {self.memory_manager.statistics}")
        print("=" * 60)
        
    async def _take_screenshot(self, prefix: str = "screen") -> str:
        """Делает скриншот и возвращает путь к файлу."""
        self.screenshot_counter += 1
        filename = f"{prefix}_{self.screenshot_counter}_{datetime.now().strftime('%H%M%S')}.png"
        filepath = await self.action_executor.take_screenshot(filename)
        return filepath
    
    async def _execute_tool(self, tool_name: str, arguments: dict) -> bool:
        """Выполняет инструмент, указанный LLM."""
        print(f"[AGENT] Выполнение инструмента: {tool_name}")
        
        try:
            if tool_name == "click_at_coordinates":
                x = arguments.get("x", 0)
                y = arguments.get("y", 0)
                button = arguments.get("button", "left")
                return await self.action_executor.click_at_coordinates(x, y, button)
                
            elif tool_name == "type_text":
                text = arguments.get("text", "")
                clear_first = arguments.get("clear_first", False)
                return await self.action_executor.type_text(text, clear_first)
                
            elif tool_name == "press_key":
                key = arguments.get("key", "")
                return await self.action_executor.press_key(key)
                
            elif tool_name == "scroll_page":
                direction = arguments.get("direction", "down")
                amount = arguments.get("amount", 300)
                return await self.action_executor.scroll_page(direction, amount)
                
            elif tool_name == "navigate_to_url":
                url = arguments.get("url", "")
                if url:
                    success = await self.action_executor.navigate_to(url)
                    if success:
                        self.memory_manager.save_memory(
                            "last_known_url", url,
                            category="navigation", priority="medium"
                        )
                    return success
                return False
                
            elif tool_name == "save_to_memory":
                category = arguments.get("category", "general")
                content = arguments.get("content", "")
                priority = arguments.get("priority", "medium")
                self.memory_manager.save_memory(
                    f"llm_save_{datetime.now().strftime('%H%M%S')}",
                    content,
                    category=category,
                    priority=priority,
                    store_long_term=(priority in ["high", "critical"])
                )
                return True
                
            elif tool_name == "query_memory":
                query = arguments.get("query", "")
                category = arguments.get("category")
                if query:
                    results = self.memory_manager.search_memories(query)
                    print(f"[MEMORY] Найдено {len(results)} воспоминаний по запросу: {query}")
                    # Сохраняем результат запроса в контекст
                    self.memory_manager.save_memory(
                        f"memory_query_{datetime.now().strftime('%H%M%S')}",
                        {"query": query, "results_count": len(results)},
                        category="memory_operation",
                        priority="low"
                    )
                return True
                
            elif tool_name == "wait_and_observe":
                duration = arguments.get("duration_seconds", 2)
                reason = arguments.get("reason", "наблюдение")
                print(f"[AGENT] Ожидание {duration}с: {reason}")
                await asyncio.sleep(duration)
                return True
                
            else:
                print(f"[AGENT WARNING] Неизвестный инструмент: {tool_name}")
                return False
                
        except Exception as e:
            print(f"[AGENT ERROR] Ошибка выполнения {tool_name}: {e}")
            return False
    
    async def _process_llm_decision(self, screenshot_path: str) -> bool:
        """Обрабатывает решение от LLM и выполняет действия."""
        # Получаем текущий контекст задачи
        task_directive = self.memory_manager.get_context('task_directive', '')
        
        # Анализируем экран через LLM
        decision = await self.llm_orchestrator.analyze_screen(
            screenshot_path,
            task_context=task_directive
        )
        
        analysis = decision.get('analysis', 'Нет анализа')
        actions = decision.get('actions', [])
        memory_operations = decision.get('memory_operations', [])
        task_complete = decision.get('task_complete', False)
        
        print(f"\n[LLM] Анализ: {analysis[:200]}..." if len(analysis) > 200 else f"\n[LLM] Анализ: {analysis}")
        print(f"[LLM] Действий: {len(actions)}, Задача завершена: {task_complete}")
        
        # Сохраняем анализ в память
        self.memory_manager.save_memory(
            f"analysis_{datetime.now().strftime('%H%M%S')}",
            {"analysis": analysis[:500], "actions_count": len(actions)},
            category="observation",
            priority="low"
        )
        
        # Выполняем действия
        for action in actions:
            tool_name = action.get('tool')
            arguments = action.get('arguments', {})
            
            if tool_name:
                success = await self._execute_tool(tool_name, arguments)
                if success:
                    print(f"[AGENT] ✓ {tool_name} выполнен успешно")
                    
                    # Сохраняем выполненное действие в память
                    self.memory_manager.save_memory(
                        f"action_{tool_name}",
                        arguments,
                        category="action",
                        priority="low"
                    )
                else:
                    print(f"[AGENT] ✗ {tool_name} не выполнен")
        
        # Обрабатываем операции с памятью
        for mem_op in memory_operations:
            # Дополнительная обработка операций с памятью
            pass
        
        # Обновляем статус задачи
        if task_complete:
            self.memory_manager.save_memory(
                "task_status",
                "completed",
                category="task",
                priority="high"
            )
        
        return task_complete
    
    async def _check_sleep_time(self) -> bool:
        """Проверяет, наступило ли время для цикла сна."""
        current_hour = datetime.now().hour
        # Например, сон в 3 часа ночи (можно настроить)
        sleep_hour = int(os.getenv("SLEEP_HOUR", "3"))
        return current_hour == sleep_hour
    
    async def _run_sleep_cycle(self) -> None:
        """Запускает цикл сна для консолидации памяти."""
        print("\n" + "=" * 60)
        print("🌙 ЗАПУСК ЦИКЛА СНА: Консолидация памяти")
        print("=" * 60)
        
        # Получаем все воспоминания для обработки
        memories = self.memory_manager.get_all_memories_for_sleep()
        print(f"[SLEEP] Обработка {len(memories)} воспоминаний...")
        
        # LLM обрабатывает воспоминания
        sleep_result = await self.llm_orchestrator.process_sleep_cycle(memories)
        
        # Применяем результаты к памяти
        self.memory_manager.consolidate_memories(sleep_result)
        
        # Очищаем краткосрочную память
        self.memory_manager.clear_short_term()
        
        # Сохраняем уроки
        lessons = sleep_result.get('lessons_learned', [])
        for lesson in lessons:
            print(f"[SLEEP] Урок: {lesson}")
        
        # Приоритеты на следующий цикл
        priorities = sleep_result.get('priorities', [])
        for priority in priorities:
            print(f"[SLEEP] Приоритет: {priority}")
        
        print("[SLEEP] Цикл сна завершен")
        print("=" * 60 + "\n")
        
        # Очищаем историю разговора LLM для нового дня
        self.llm_orchestrator.clear_conversation_history()
    
    async def run_autonomous_loop(self, max_iterations: Optional[int] = None) -> None:
        """
        Запускает автономный цикл работы агента.
        
        Args:
            max_iterations: Максимальное количество итераций (None для бесконечного цикла)
        """
        print("\n--- [AGENT] ВХОД В ПРОАКТИВНЫЙ ЦИКЛ ---\n")
        
        iteration = 0
        last_sleep_check = datetime.now()
        
        while self.running:
            try:
                iteration += 1
                print(f"\n{'='*40}")
                print(f"[ЦИКЛ {iteration}] Начало итерации")
                print(f"{'='*40}")
                
                # Проверка времени для сна
                time_since_check = (datetime.now() - last_sleep_check).total_seconds()
                if time_since_check > 3600:  # Проверяем каждый час
                    if await self._check_sleep_time():
                        await self._run_sleep_cycle()
                    last_sleep_check = datetime.now()
                
                # Делаем скриншот текущего экрана
                screenshot_path = await self._take_screenshot()
                print(f"[AGENT] Скриншот сохранен: {screenshot_path}")
                
                # Отправляем на анализ LLM
                task_completed = await self._process_llm_decision(screenshot_path)
                
                # Сохраняем текущее состояние
                current_url = await self.action_executor.get_page_url()
                self.memory_manager.save_memory(
                    "last_known_url",
                    current_url,
                    category="context",
                    priority="medium"
                )
                
                # Пауза между итерациями (чтобы не спамить API)
                wait_time = int(os.getenv("AGENT_LOOP_DELAY", "5"))
                print(f"[AGENT] Ожидание {wait_time}с перед следующей итерацией...")
                await asyncio.sleep(wait_time)
                
                # Проверка максимального количества итераций
                if max_iterations and iteration >= max_iterations:
                    print(f"[AGENT] Достигнуто максимальное количество итераций: {max_iterations}")
                    break
                    
            except KeyboardInterrupt:
                print("\n[AGENT] Прервано пользователем")
                break
            except Exception as e:
                print(f"[AGENT ERROR] Критическая ошибка в цикле: {e}")
                # Делаем скриншот ошибки
                await self._take_screenshot("error")
                # Продолжаем работу после паузы
                await asyncio.sleep(10)
        
        print("\n[AGENT] Автономный цикл завершен")
    
    async def set_task(self, task_description: str) -> None:
        """Устанавливает задачу для агента."""
        self.task_context = task_description
        self.memory_manager.save_memory(
            "task_directive",
            task_description,
            category="task",
            priority="high",
            store_long_term=True
        )
        print(f"[AGENT] Задача установлена: {task_description}")
    
    async def shutdown(self) -> None:
        """Корректное завершение работы агента."""
        print("\n[AGENT] Завершение работы...")
        self.running = False
        
        # Финальное сохранение состояния
        current_url = await self.action_executor.get_page_url()
        self.memory_manager.save_memory(
            "session_end_url",
            current_url,
            category="context",
            priority="medium"
        )
        
        # Закрываем браузер
        await self.action_executor.close()
        
        # Печатаем финальную статистику
        print(f"\n{'='*60}")
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        print(f"{'='*60}")
        stats = self.memory_manager.statistics
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print(f"{'='*60}\n")


async def main():
    """Главная точка входа."""
    # Создаем агента
    agent = AutonomousAgent(
        headless=False,  # False для визуального наблюдения
        sleep_cycle_hours=6
    )
    
    try:
        # Инициализация
        await agent.initialize()
        
        # Установка задачи (опционально)
        # await agent.set_task("Найти информацию о Python программировании и сохранить важные ссылки")
        
        # Запуск автономного цикла
        # max_iterations=None для бесконечной работы
        await agent.run_autonomous_loop(max_iterations=10)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Критическая ошибка агента: {e}")
        await agent.shutdown()
        raise
    finally:
        # Гарантированное завершение
        await agent.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[EXIT] Агент остановлен пользователем.")

