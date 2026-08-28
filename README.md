# Events Aggregator

Backend-сервис для работы с событиями.

Сервис получает события из внешнего Events Provider API, сохраняет их в PostgreSQL и предоставляет своё REST API для просмотра событий, свободных мест, регистрации и отмены билетов.

## Стек

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- httpx
- Pydantic
- Docker / Docker Compose
- pytest
- Ruff
- GitHub Actions

## Возможности

- получение списка событий;
- получение информации об отдельном событии;
- фильтрация событий по дате;
- пагинация;
- ручная синхронизация событий;
- автоматическая синхронизация раз в сутки;
- получение свободных мест из внешнего API;
- кэширование свободных мест на 30 секунд;
- регистрация на событие;
- отмена регистрации.

## API

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/api/health` | Проверка работы сервиса |
| POST | `/api/sync/trigger` | Ручная синхронизация событий |
| GET | `/api/events` | Получение списка событий |
| GET | `/api/events/{event_id}` | Получение информации о событии |
| GET | `/api/events/{event_id}/seats` | Получение свободных мест |
| POST | `/api/tickets` | Регистрация на событие |
| DELETE | `/api/tickets/{ticket_id}` | Отмена регистрации |

Swagger после запуска приложения:

```text
http://localhost:8000/docs
```

## Переменные окружения

Для локального запуска необходимо создать файл `.env`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=events
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

EVENTS_PROVIDER_BASE_URL=provider_url
EVENTS_PROVIDER_API_KEY=api_key
```

Файл `.env` добавлен в `.gitignore` и не должен попадать в репозиторий.

## Запуск проекта

Установить зависимости:

```bash
uv sync
```

Запустить приложение и PostgreSQL через Docker Compose:

```bash
docker compose up --build
```

После запуска сервис будет доступен по адресу:

```text
http://localhost:8000
```

Проверка:

```text
http://localhost:8000/api/health
```

## Миграции

Для миграций используется Alembic.

Применить миграции вручную:

```bash
uv run alembic upgrade head
```

При запуске приложения через Docker миграции выполняются автоматически перед запуском сервиса.

## Тесты

Запустить тесты:

```bash
uv run pytest
```

## Ruff

Проверить код:

```bash
uv run ruff check .
```

## CI/CD

В проекте настроен GitHub Actions.

При push в ветку `main` выполняются:

- проверка Ruff;
- запуск тестов;
- сборка Docker-образа;
- публикация образа;
- запрос на деплой.

Если Ruff или тесты завершаются с ошибкой, следующие этапы не запускаются.