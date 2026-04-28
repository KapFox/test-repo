#!/usr/bin/env python
"""
LLM Orchestrator - Мозг автономного RPA-агента
Отвечает за взаимодействие с LLM API, анализ скриншотов и принятие решений
"""
import base64
import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class LLMOrchestrator:
    """
    Оркестратор на базе LLM для анализа экрана и принятия решений.
    Поддерживает мультимодальный ввод (скриншоты + текст) и проактивное использование инструментов.
    """
    
    def __init__(self, api_key: str = "not-needed", base_url: str = "http://localhost:1234/v1", model: str = "gemma-2-9b-it"):
        """
        Инициализация LLM оркестратора.
        
        :param api_key: API ключ (для LM Studio можно использовать любое значение, например 'not-needed')
        :param base_url: Базовый URL API. По умолчанию локальный сервер LM Studio.
        :param model: Название модели. Для LM Studio должно совпадать с загруженной моделью (например, 'gemma-2-9b-it').
        """
        self.api_key = api_key
        self.api_base_url = base_url.rstrip('/')
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        self.available_tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Определяет доступные инструменты для LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "click_at_coordinates",
                    "description": "Кликнуть в указанные координаты на экране",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "X координата (пиксели)"},
                            "y": {"type": "integer", "description": "Y координата (пиксели)"},
                            "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Кнопка мыши"}
                        },
                        "required": ["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description": "Ввести текст в текущее поле ввода",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Текст для ввода"},
                            "clear_first": {"type": "boolean", "description": "Очистить поле перед вводом"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "press_key",
                    "description": "Нажать клавишу или комбинацию клавиш",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Клавиша (например, 'Enter', 'Tab', 'Control+a')"}
                        },
                        "required": ["key"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scroll_page",
                    "description": "Прокрутить страницу",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {"type": "string", "enum": ["up", "down"], "description": "Направление прокрутки"},
                            "amount": {"type": "integer", "description": "Количество пикселей"}
                        },
                        "required": ["direction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "navigate_to_url",
                    "description": "Перейти по URL адресу",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL для перехода"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_to_memory",
                    "description": "Сохранить важную информацию в долговременную память",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "Категория памяти (task, observation, learning, etc.)"},
                            "content": {"type": "string", "description": "Содержание для сохранения"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Приоритет воспоминания"}
                        },
                        "required": ["category", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_memory",
                    "description": "Запросить информацию из долговременной памяти",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Поисковый запрос к памяти"},
                            "category": {"type": "string", "description": "Фильтр по категории"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wait_and_observe",
                    "description": "Подождать указанное время и сделать новый скриншот для наблюдения",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration_seconds": {"type": "number", "description": "Длительность ожидания в секундах"},
                            "reason": {"type": "string", "description": "Причина ожидания"}
                        },
                        "required": ["duration_seconds"]
                    }
                }
            }
        ]
    
    def encode_screenshot(self, screenshot_path: str) -> str:
        """Кодирует скриншот в base64 для отправки в LLM."""
        with open(screenshot_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def analyze_screen(self, screenshot_path: str, task_context: str = "") -> Dict[str, Any]:
        """
        Анализирует скриншот экрана через LLM API.
        Возвращает решение о следующих действиях с координатами и инструментами.
        """
        # Для LM Studio API ключ не обязателен
        if not self.api_key or self.api_key == "not-needed":
            print("[LLM_ORCHESTRATOR] Работа с локальным API (LM Studio)")
        
        screenshot_base64 = self.encode_screenshot(screenshot_path)
        
        system_prompt = """Ты - автономный RPA-агент с искусственным интеллектом. 
Твоя задача - анализировать экран компьютера и выполнять задачи проактивно.

Ты имеешь доступ к следующим инструментам:
- click_at_coordinates: Клик в точку экрана
- type_text: Ввод текста
- press_key: Нажатие клавиш
- scroll_page: Прокрутка страницы
- navigate_to_url: Переход по URL
- save_to_memory: Сохранение в память
- query_memory: Запрос к памяти
- wait_and_observe: Ожидание и наблюдение

Правила:
1. Анализируй экран внимательно, определяй интерактивные элементы
2. Действуй проактивно - не жди указаний, если видишь что можно сделать
3. Используй память для сохранения важной информации
4. Если задача выполнена - сообщи об этом
5. Координаты должны быть в пределах экрана (обычно 0-1920 по X, 0-1080 по Y)
6. Будь точным в координатах - кликай в центр элементов

Форматируй ответ как JSON с полями:
- analysis: краткий анализ того, что на экране
- reasoning: логика принятия решения
- actions: список действий для выполнения (массив)
- memory_operations: операции с памятью если нужны
- task_complete: boolean, завершена ли текущая задача
"""
        
        user_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Текущая задача: {task_context}\n\nПроанализируй этот скриншот и определи следующие действия."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ]
        }
        
        self.conversation_history.append(user_message)
        
        try:
            import aiohttp
            headers = {
                "Content-Type": "application/json"
            }
            # Для LM Studio Authorization header не обязателен, но можно добавить если нужен
            if self.api_key and self.api_key != "not-needed":
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *self.conversation_history[-10:]  # Последние 10 сообщений для контекста
                ],
                "tools": self.available_tools,
                "tool_choice": "auto",
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        print(f"[LLM_ORCHESTRATOR ERROR] API вернул ошибку: {result}")
                        return self._mock_analyze_screen(screenshot_path, task_context)
                    
                    message = result["choices"][0]["message"]
                    
                    # Сохраняем ответ ассистента в историю
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": message.get("content", ""),
                        "tool_calls": message.get("tool_calls", [])
                    })
                    
                    return self._parse_llm_response(message)
                    
        except Exception as e:
            print(f"[LLM_ORCHESTRATOR ERROR] Ошибка при вызове LLM API: {e}")
            return self._mock_analyze_screen(screenshot_path, task_context)
    
    def _parse_llm_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит ответ от LLM и извлекает действия."""
        actions = []
        memory_operations = []
        
        tool_calls = message.get("tool_calls", [])
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            func_name = function.get("name")
            func_args = json.loads(function.get("arguments", "{}"))
            
            if func_name:
                actions.append({
                    "tool": func_name,
                    "arguments": func_args
                })
        
        # Также пытаемся извлечь действия из текстового ответа
        content = message.get("content", "")
        if content:
            try:
                # Пытаемся найти JSON в тексте
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group())
                    if "actions" in parsed:
                        actions.extend(parsed["actions"])
                    if "memory_operations" in parsed:
                        memory_operations.extend(parsed["memory_operations"])
            except json.JSONDecodeError:
                pass
        
        return {
            "analysis": message.get("content", ""),
            "actions": actions,
            "memory_operations": memory_operations,
            "task_complete": False  # По умолчанию
        }
    
    def _mock_analyze_screen(self, screenshot_path: str, task_context: str = "") -> Dict[str, Any]:
        """Mock-режим для тестирования без API ключа."""
        print("[LLM_ORCHESTRATOR] Работа в mock-режиме (без API ключа)")
        return {
            "analysis": "Mock анализ: на экране отображается веб-страница",
            "reasoning": "Mock режим - симуляция решения",
            "actions": [
                {"tool": "wait_and_observe", "arguments": {"duration_seconds": 2, "reason": "mock observation"}}
            ],
            "memory_operations": [],
            "task_complete": False
        }
    
    async def process_sleep_cycle(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Обрабатывает воспоминания во время 'сна' агента.
        Структурирует память, выделяет важное, удаляет шум.
        """
        # Для LM Studio API ключ не обязателен
        if not self.api_key or self.api_key == "not-needed":
            print("[LLM_ORCHESTRATOR] Обработка сна через локальное API (LM Studio)")
        
        system_prompt = """Ты - система консолидации памяти автономного агента.
Твоя задача - обработать воспоминания за день и структурировать их.

Что нужно сделать:
1. Выделить важные воспоминания (высокий приоритет)
2. Сгруппировать связанные воспоминания
3. Извлечь уроки и паттерны
4. Отметить воспоминания для долгосрочного хранения
5. Идентифицировать шум и маловажные данные

Верни результат в формате JSON:
- consolidated_memories: список обработанных воспоминаний
- lessons_learned: извлеченные уроки
- priorities: приоритеты на следующий цикл
- to_forget: что можно забыть (шум)
"""
        
        memories_text = "\n".join([
            f"- {m.get('timestamp', 'N/A')}: [{m.get('category', 'general')}] {m.get('content', '')} (priority: {m.get('priority', 'medium')})"
            for m in memories
        ])
        
        try:
            import aiohttp
            headers = {
                "Content-Type": "application/json"
            }
            # Для LM Studio Authorization header не обязателен, но можно добавить если нужен
            if self.api_key and self.api_key != "not-needed":
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Обработай эти воспоминания:\n\n{memories_text}"}
                ],
                "max_tokens": 3000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        print(f"[LLM_ORCHESTRATOR ERROR] API вернул ошибку при обработке сна: {result}")
                        return self._mock_sleep_process(memories)
                    
                    content = result["choices"][0]["message"].get("content", "")
                    
                    try:
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass
                    
                    return {"raw_analysis": content}
                    
        except Exception as e:
            print(f"[LLM_ORCHESTRATOR ERROR] Ошибка при обработке сна: {e}")
            return self._mock_sleep_process(memories)
    
    def _mock_sleep_process(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock-обработка сна."""
        return {
            "consolidated_memories": memories[:5],  # Оставляем только первые 5
            "lessons_learned": ["Mock урок: система работает корректно"],
            "priorities": ["continue_current_task"],
            "to_forget": []
        }
    
    def clear_conversation_history(self):
        """Очищает историю разговора для нового сеанса."""
        self.conversation_history = []
        print("[LLM_ORCHESTRATOR] История разговора очищена.")
