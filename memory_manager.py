#!/usr/bin/env python
import json
from datetime import datetime
import os

class MemoryManager:
    """
    Управляет постоянным состоянием и контекстом автономного агента.
    Состояние сохраняется в локальный файл (например, 'agent_state.json').
    """
    def __init__(self, state_file='agent_state.json'):
        self.state_file = state_file
        self.memory = self._load_memory()

    def _load_memory(self):
        """Загружает память из локального файла."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[MEMORY ERROR] Не удалось загрузить память из {self.state_file}: {e}. Начинаем со свежим состоянием.")
                return {"history": [], "context": {}, "session_status": "initial"}
        else:
            return {"history": [], "context": {}, "session_status": "initial"}

    def save_memory(self, key: str, value):
        """Обновляет определенную часть контекста и сохраняет состояние."""
        if isinstance(value, dict): 
            self.memory['context'].update(value)
        else:
             self.memory['context'][key] = value
        
        self.memory['history'].append({"timestamp": datetime.now().isoformat(), "action": key, "result_summary": str(value)[:100]})
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=4)
            print(f"[MEMORY] Состояние успешно сохранено в {self.state_file}.")
        except IOError as e:
            print(f"[MEMORY ERROR] Не удалось сохранить состояние: {e}")

    def get_context(self, key: str): 
        """Извлекает конкретный контекст."""
        return self.memory['context'].get(key)

    @property
    def current_status(self) -> str:
        """Возвращает текущий статус сессии."""
        return self.memory['context'].get('session_status', 'initial')