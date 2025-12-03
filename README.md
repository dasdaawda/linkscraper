# LinkedIn Invitation Scraper с логированием

Автоматический сбор всех ссылок на профили LinkedIn людей, которым были отправлены запросы на подписку от вашей организации.

## Основные возможности

- ✅ Использует существующую авторизованную сессию браузера (не требует паролей)
- ✅ Обрабатывает бесконечный скролл страницы
- ✅ Логирование прогресса в `logs/scraper.log`
- ✅ Отдельный лог для неразобранных элементов `logs/unparsed_items.log`
- ✅ Дедупликация URL
- ✅ Resume-функция: продолжение с места остановки через `data/state.json`
- ✅ Выходные файлы: CSV и XLSX
- ✅ Имитация человеческих действий (случайные задержки, скроллинг)
- ✅ UTF-8 кодировка для корректного отображения русских символов

## Требования

- Python 3.9+
- Playwright для автоматизации браузера
- Pandas и openpyxl для экспорта данных

## Установка

### 1. Клонируйте репозиторий
```bash
git clone <repository-url>
cd linkscraper
```

### 2. Установите зависимости
```bash
pip install -r requirements.txt
```

### 3. Установите браузеры Playwright
```bash
playwright install chromium
```

## Использование

### Способ 1: CLI с аргументами

#### Минимальный запуск
```bash
python main.py --user-data-dir /path/to/chrome/profile
```

#### Полная команда со всеми параметрами
```bash
python main.py \
    --user-data-dir /path/to/chrome/profile \
    --target-url "https://www.linkedin.com/mynetwork/invitation-manager/sent/YOUR_ORG/" \
    --output-csv output.csv \
    --output-xlsx output.xlsx \
    --resume-state data/state.json \
    --headless
```

### Способ 2: Python скрипт

Создайте файл `run_scraper.py`:

```python
from pathlib import Path
from linkscraper.config import ScraperConfig
from linkscraper.scrapers.linkedin_invitations import LinkedInInvitationsScraper

config = ScraperConfig(
    target_url="https://www.linkedin.com/mynetwork/invitation-manager/sent/ORGANIZATION/",
    output_csv=Path("output.csv"),
    output_xlsx=Path("output.xlsx"),
    user_data_dir=Path("/path/to/chrome/profile"),
    headless=False,
)

scraper = LinkedInInvitationsScraper(config)
scraper.run()
```

Запустите:
```bash
python run_scraper.py
```

### Способ 3: Использование переменной окружения

```bash
export LINKEDIN_USER_DATA_DIR="/path/to/chrome/profile"
python main.py
```

## Получение пути к профилю Chrome

### Windows
```
%LOCALAPPDATA%\Google\Chrome\User Data
```

### macOS
```
~/Library/Application Support/Google/Chrome
```

### Linux
```
~/.config/google-chrome
```

**Важно:** Закройте Chrome перед запуском скрейпера или используйте отдельный профиль.

## Выходные данные

### Формат файлов (CSV/XLSX)

Оба файла содержат 4 столбца:

| Столбец | Описание | Пример |
|---------|----------|--------|
| `profile_name` | Имя профиля | "John Doe" |
| `profile_url` | URL профиля | "https://www.linkedin.com/in/johndoe/" |
| `invitation_date` | Дата отправки | "Sent today", "Sent 2 days ago" |
| `invited_to` | Приглашение | "Invited to follow TechCorp" |

### Логи

#### `logs/scraper.log`
Содержит:
- Время начала и завершения работы
- Количество собранных записей (всего, уникальных, дубликатов)
- Количество скроллов страницы
- Время выполнения
- Ошибки и исключения с полным трейсом
- Прогресс в реальном времени

Пример:
```
2024-01-15 10:30:00 - INFO - ================================================================================
2024-01-15 10:30:00 - INFO - LinkedIn Invitations Scraper Started
2024-01-15 10:30:00 - INFO - ================================================================================
2024-01-15 10:30:00 - INFO - Start time: 2024-01-15 10:30:00
2024-01-15 10:30:00 - INFO - Target URL: https://www.linkedin.com/mynetwork/invitation-manager/sent/...
2024-01-15 10:30:05 - INFO - Browser session started
2024-01-15 10:30:10 - INFO - Progress: 10 unique invitations collected (+10)
2024-01-15 10:30:15 - INFO - Progress: 25 unique invitations collected (+15)
...
2024-01-15 10:35:00 - INFO - Scraping Completed
2024-01-15 10:35:00 - INFO - Total duration: 0:05:00
2024-01-15 10:35:00 - INFO - Statistics:
2024-01-15 10:35:00 - INFO -   Total items collected: 150
2024-01-15 10:35:00 - INFO -   Unique items: 150
2024-01-15 10:35:00 - INFO -   Duplicates: 0
2024-01-15 10:35:00 - INFO -   Page scrolls: 45
```

#### `logs/unparsed_items.log`
Создаётся только при наличии ошибок парсинга. Содержит:
- Номер ошибки
- Причину ошибки
- HTML-фрагмент проблемного элемента (первые 500 символов)
- Полный HTML (первые 2000 символов)

## Настройка параметров

Основные параметры можно изменить в `linkscraper/config.py`:

```python
@dataclass
class ScraperConfig:
    # Задержки между скроллами (сек)
    scroll_pause_range: Tuple[float, float] = (1.0, 3.0)
    
    # Задержки перед кликами (сек)
    click_delay_range: Tuple[float, float] = (0.5, 1.5)
    
    # Вероятность "замирания" при скролле
    freeze_chance: float = 0.25
    
    # Длительность "замирания" (сек)
    freeze_duration_range: Tuple[float, float] = (2.0, 4.0)
    
    # Интервал вывода прогресса (каждые N элементов)
    progress_interval: int = 5
    
    # Количество скроллов без новых данных перед остановкой
    max_scrolls_without_new_content: int = 5
    
    # Количество скроллов за один батч
    scroll_batch_size: int = 3
```

## Resume-функционал

Скрейпер автоматически сохраняет состояние в `data/state.json`. При повторном запуске:
- Пропускает уже собранные URL
- Продолжает с места остановки
- Добавляет новые записи в существующие файлы

Для начала с нуля удалите:
```bash
rm data/state.json
rm output.csv
rm output.xlsx
```

## Troubleshooting

### Проблема: "Session not authenticated"
**Решение:** Убедитесь, что вы авторизованы в LinkedIn в профиле браузера, путь к которому указан в `--user-data-dir`.

### Проблема: "No invitations found"
**Возможные причины:**
1. Неверный URL (замените `ORGANIZATION` на реальный ID организации)
2. Нет отправленных приглашений
3. LinkedIn изменил структуру страницы

**Решение:** Проверьте `logs/scraper.log` и `logs/unparsed_items.log` для деталей.

### Проблема: LinkedIn блокирует запросы
**Решение:**
1. Увеличьте задержки в `config.py`
2. Уменьшите `scroll_batch_size`
3. Используйте `headless=False` для визуального контроля

### Проблема: Браузер не запускается
**Решение:**
1. Закройте все экземпляры Chrome
2. Используйте другой профиль браузера
3. Проверьте права доступа к директории профиля

### Проблема: Кодировка в CSV
**Решение:** Откройте CSV в Excel:
1. File → Import → CSV file
2. Выберите кодировку UTF-8
3. Или используйте XLSX файл напрямую

## Структура проекта

```
linkscraper/
├── scrapers/
│   └── linkedin_invitations.py      # Основной скрейпер
├── utils/
│   ├── browser_session.py           # Работа с браузером (Playwright)
│   ├── logger.py                    # Логирование
│   └── deduplicator.py              # Дедупликация URL
├── config.py                        # Конфигурация
└── main.py                          # Точка входа (CLI)
main.py                              # Точка входа (корень)
requirements.txt                     # Зависимости
README.md                            # Документация
example.py                           # Пример использования
```

## Лицензия

MIT License

## Важные замечания

⚠️ **Использование скрейпера может нарушать Terms of Service LinkedIn. Используйте на свой страх и риск.**

⚠️ **Не запускайте скрейпер слишком часто - это может привести к блокировке аккаунта.**

⚠️ **Убедитесь, что у вас есть права на сбор данных в соответствии с GDPR и другими законами о защите данных.**
