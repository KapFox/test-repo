# Настройка для LM Studio и Gemma

## 🔧 Конфигурация环境变量

Для работы с **LM Studio** и моделью **Gemma** установите следующие переменные окружения:

```bash
# API ключ (для LM Studio можно использовать любое значение)
export LLM_API_KEY="not-needed"

# URL локального сервера LM Studio (по умолчанию порт 1234)
export LLM_BASE_URL="http://localhost:1234/v1"

# Название модели (должно совпадать с загруженной в LM Studio)
# Для Gemma 2 9B Instruction:
export LLM_MODEL="gemma-2-9b-it"

# Или для других версий Gemma:
# export LLM_MODEL="gemma-7b-it"
# export LLM_MODEL="gemma2-9b-it"
```

### Windows (PowerShell):
```powershell
$env:LLM_API_KEY="not-needed"
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_MODEL="gemma-2-9b-it"
```

### Windows (CMD):
```cmd
set LLM_API_KEY=not-needed
set LLM_BASE_URL=http://localhost:1234/v1
set LLM_MODEL=gemma-2-9b-it
```

## 📋 Запуск LM Studio

1. **Скачайте и установите** [LM Studio](https://lmstudio.ai/)
2. **Загрузите модель Gemma**:
   - Откройте LM Studio
   - В поиске найдите "gemma 2 9b instruct"
   - Скачайте подходящую квантованную версию (рекомендуется Q4_K_M или Q5_K_M)
3. **Запустите локальный сервер**:
   - Перейдите во вкладку "Local Server" (↔️)
   - Выберите загруженную модель Gemma
   - Нажмите "Start Server"
   - Убедитесь, что сервер слушает порт `1234`

4. **Настройте CORS** (если требуется):
   - В настройках сервера включите CORS
   - Это позволит браузеру делать запросы к API

## 🚀 Запуск агента

После настройки LM Studio запустите агента:

```bash
python main.py
```

Или с явными параметрами:

```bash
LLM_BASE_URL="http://localhost:1234/v1" LLM_MODEL="gemma-2-9b-it" python main.py
```

## ⚙️ Дополнительные настройки

### Порт сервера
Если LM Studio использует другой порт, измените `LLM_BASE_URL`:
```bash
export LLM_BASE_URL="http://localhost:8080/v1"
```

### Модель
Проверьте точное название модели в LM Studio (отображается в интерфейсе):
```bash
export LLM_MODEL="точное-название-модели-как-в-lm-studio"
```

### Режим без головки (headless)
Для работы без отображения браузера:
```python
# В main.py измените:
agent = AutonomousAgent(headless=True, ...)
```

## 🔍 Проверка подключения

Убедитесь, что LM Studio сервер доступен:

```bash
curl http://localhost:1234/v1/models
```

Должен вернуться JSON со списком моделей.

## 🛠️ Решение проблем

### Ошибка подключения
- Убедитесь, что LM Studio запущен
- Проверьте, что сервер активен (кнопка "Stop Server" видна)
- Проверьте порт в настройках LM Studio

### Модель не отвечает
- Убедитесь, что модель полностью загружена
- Попробуйте меньшую квантованную версию (Q3_K_S, Q4_K_S)
- Увеличьте timeout в настройках LM Studio

### Ошибки CORS
- Включите CORS в настройках LM Studio Server
- Или используйте флаг `--disable-cors` при запуске

### Model not found
- Проверьте точное название модели в LM Studio
- Убедитесь, что модель загружена и выбрана в сервере
- Перезапустите сервер LM Studio

## 📝 Пример .env файла

Создайте файл `.env` в корне проекта:

```env
# LLM Configuration for LM Studio + Gemma
LLM_API_KEY=not-needed
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=gemma-2-9b-it

# Agent Settings
START_URL=https://www.google.com
SLEEP_HOUR=3
AGENT_LOOP_DELAY=5
```

Затем установите пакет python-dotenv:
```bash
pip install python-dotenv
```

И добавьте в начало `main.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

## 🎯 Рекомендации для Gemma

1. **Контекст**: Gemma 2 9B хорошо работает с контекстом до 4096 токенов
2. **Точность**: Используйте Q5_K_M или выше для лучших результатов
3. **Скорость**: Q4_K_M обеспечивает хороший баланс скорость/качество
4. **Память**: Требуется минимум 8GB RAM для Q4, 12GB+ для Q5/Q6

## 📊 Мониторинг

В логах вы увидите:
```
🔧 КОНФИГУРАЦИЯ LLM
============================================================
API Key: не требуется (LM Studio)
Base URL: http://localhost:1234/v1
Model: gemma-2-9b-it
============================================================
```

Это подтверждает правильную настройку подключения к LM Studio!
