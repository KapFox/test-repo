#!/usr/bin/env python
"""
Memory Manager - Система управления памятью автономного агента
Поддерживает краткосрочную и долгосрочную память, приоритеты, консолидацию
"""
import json
from datetime import datetime
import os
from typing import Dict, Any, List, Optional


class MemoryManager:
    """
    Управляет постоянным состоянием и контекстом автономного агента.
    Состояние сохраняется в локальный файл (agent_state.json).
    Поддерживает категоризацию, приоритеты и временные метки.
    """
    
    def __init__(self, state_file: str = 'agent_state.json'):
        self.state_file = state_file
        self.memory = self._load_memory()
        
    def _load_memory(self) -> Dict[str, Any]:
        """Загружает память из локального файла."""
        default_memory = {
            "context": {},
            "short_term_memories": [],
            "long_term_memories": [],
            "consolidated_memories": [],
            "lessons_learned": [],
            "session_history": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "sleep_cycles": 0
            }
        }
        
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Объединяем с дефолтной структурой
                    for key in default_memory:
                        if key not in loaded:
                            loaded[key] = default_memory[key]
                    return loaded
            except (json.JSONDecodeError, IOError) as e:
                print(f"[MEMORY ERROR] Не удалось загрузить память: {e}. Начинаем со свежим состоянием.")
                return default_memory
        else:
            return default_memory

    def save_memory(self, key: str, value: Any, category: str = "general", 
                    priority: str = "medium", store_long_term: bool = False) -> None:
        """
        Сохраняет информацию в память с категорией и приоритетом.
        
        Args:
            key: Ключ памяти
            value: Значение
            category: Категория (task, observation, learning, action, etc.)
            priority: Приоритет (low, medium, high, critical)
            store_long_term: Сохранять ли в долгосрочную память
        """
        timestamp = datetime.now().isoformat()
        
        memory_entry = {
            "timestamp": timestamp,
            "key": key,
            "value": value,
            "category": category,
            "priority": priority,
            "content": str(value)[:500]  # Краткое содержание для быстрого просмотра
        }
        
        # Обновляем контекст
        if isinstance(value, dict):
            self.memory['context'].update(value)
        else:
            self.memory['context'][key] = value
        
        # Добавляем в краткосрочную память
        self.memory['short_term_memories'].append(memory_entry)
        
        # Если важно - добавляем в долгосрочную
        if store_long_term or priority in ["high", "critical"]:
            self.memory['long_term_memories'].append(memory_entry)
        
        # Добавляем в историю сессии
        self.memory['session_history'].append({
            "timestamp": timestamp,
            "action": key,
            "category": category,
            "result_summary": str(value)[:100]
        })
        
        # Обновляем метаданные
        self.memory['metadata']['last_updated'] = timestamp
        
        # Ограничиваем размер краткосрочной памяти (последние 100 записей)
        if len(self.memory['short_term_memories']) > 100:
            self.memory['short_term_memories'] = self.memory['short_term_memories'][-100:]
        
        self._save_to_file()
        print(f"[MEMORY] Сохранено: {key} (категория: {category}, приоритет: {priority})")

    def _save_to_file(self) -> None:
        """Сохраняет память в файл."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[MEMORY ERROR] Не удалось сохранить состояние: {e}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """Извлекает конкретный контекст."""
        return self.memory['context'].get(key, default)

    def get_memories_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает воспоминания по категории."""
        all_memories = (
            self.memory['short_term_memories'] + 
            self.memory['long_term_memories']
        )
        filtered = [m for m in all_memories if m.get('category') == category]
        # Сортируем по времени (новые первые)
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return filtered[:limit]

    def get_memories_by_priority(self, priority: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает воспоминания по приоритету."""
        all_memories = (
            self.memory['short_term_memories'] + 
            self.memory['long_term_memories']
        )
        filtered = [m for m in all_memories if m.get('priority') == priority]
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return filtered[:limit]

    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск воспоминаний по содержимому."""
        all_memories = (
            self.memory['short_term_memories'] + 
            self.memory['long_term_memories'] +
            self.memory['consolidated_memories']
        )
        query_lower = query.lower()
        
        results = []
        for memory in all_memories:
            content = str(memory.get('content', '')).lower()
            key = str(memory.get('key', '')).lower()
            value = str(memory.get('value', '')).lower()
            
            if query_lower in content or query_lower in key or query_lower in value:
                results.append(memory)
        
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results[:limit]

    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает последние воспоминания."""
        all_memories = self.memory['short_term_memories'][-limit:]
        all_memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_memories

    def add_lesson_learned(self, lesson: str) -> None:
        """Добавляет извлеченный урок."""
        self.memory['lessons_learned'].append({
            "timestamp": datetime.now().isoformat(),
            "lesson": lesson
        })
        self._save_to_file()

    def consolidate_memories(self, sleep_result: Dict[str, Any]) -> None:
        """
        Применяет результаты цикла сна к памяти.
        Вызывается после process_sleep_cycle().
        """
        consolidated = sleep_result.get('consolidated_memories', [])
        lessons = sleep_result.get('lessons_learned', [])
        to_forget = sleep_result.get('to_forget', [])
        
        # Добавляем консолидированные воспоминания
        self.memory['consolidated_memories'].extend(consolidated)
        
        # Добавляем уроки
        for lesson in lessons:
            self.add_lesson_learned(lesson)
        
        # Удаляем ненужное (помечаем)
        for forget_item in to_forget:
            # В реальной реализации можно удалить из short_term
            pass
        
        # Увеличиваем счетчик циклов сна
        self.memory['metadata']['sleep_cycles'] = \
            self.memory['metadata'].get('sleep_cycles', 0) + 1
        
        self._save_to_file()
        print(f"[MEMORY] Консолидация завершена. Циклов сна: {self.memory['metadata']['sleep_cycles']}")

    def get_all_memories_for_sleep(self) -> List[Dict[str, Any]]:
        """Получает все воспоминания для обработки во время сна."""
        return (
            self.memory['short_term_memories'] + 
            self.memory['long_term_memories']
        )

    @property
    def current_status(self) -> str:
        """Возвращает текущий статус сессии."""
        return self.memory['context'].get('session_status', 'initial')

    @property
    def statistics(self) -> Dict[str, int]:
        """Возвращает статистику памяти."""
        return {
            "short_term_count": len(self.memory['short_term_memories']),
            "long_term_count": len(self.memory['long_term_memories']),
            "consolidated_count": len(self.memory['consolidated_memories']),
            "lessons_count": len(self.memory['lessons_learned']),
            "sleep_cycles": self.memory['metadata'].get('sleep_cycles', 0)
        }

    def clear_short_term(self) -> None:
        """Очищает краткосрочную память (после консолидации)."""
        self.memory['short_term_memories'] = []
        self._save_to_file()
        print("[MEMORY] Краткосрочная память очищена.")