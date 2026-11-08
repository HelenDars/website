# NORDIS

Платформа единого управления бизнесом для собственников (Казахстан).
Многоклиентская: каждый клиент — отдельный `tenant`, данные разделены
на уровне базы (row-level security). Техническое задание — [`docs/NORDIS_ТЗ.md`](docs/NORDIS_ТЗ.md).

## Состав

| Сервис | Что делает |
|---|---|
| `api` | FastAPI: REST для приложения и админки |
| `worker` | Celery: загрузки данных, расчёт показателей, брифинги |
| `beat` | Расписание фоновых задач |
| `db` | PostgreSQL 16 |
| `redis` | Очередь задач |

Структура `backend/app/` повторяет раздел 2.3 ТЗ: `api`, `connectors`, `ingest`,
`metrics`, `agents`, `rules`, `billing`, `notify`, `security`.

## Запуск

```bash
cp .env.example .env      # заполнить пароли
docker compose up --build
```

Проверка: `http://localhost:8000/health/ready` → `{"status": "ok", ...}`.
Документация API: `http://localhost:8000/docs`.

## Тесты

```bash
docker compose up -d db redis
cd backend && pip install -e ".[dev]" && pytest
```

## Правила

- Реальные данные клиентов в репозиторий не попадают: папка `data/` и файлы Excel/CSV в `.gitignore`.
- Ключи и пароли — только через переменные окружения (`.env`).
