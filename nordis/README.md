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

## Разделение клиентов

- Каждая клиентская таблица содержит `tenant_id` и защищена row-level security PostgreSQL.
- С данными клиента код работает только через `tenant_session(tenant_id)` (`app/db.py`):
  транзакция переключается в роль `nordis_app`, которая не может обойти защиту,
  и видит только строки этого клиента. Без указанного клиента не видно ничего.
- `admin_session()` — только для админки NORDIS (создание клиентов, общий справочник).
- Тест `tests/test_tenant_isolation.py` проверяет чтение, запись и изменение чужих
  данных, а также что у каждой таблицы с `tenant_id` включена защита.

Схема — миграция `backend/migrations/versions/0001_core_schema.py`.
Суммы хранятся как `numeric(18,2)` (тенге с тиынами), чтобы сверка с ОПиУ
сходилась до тенге. Налоговый режим и отрасль — в карточке клиента
(`tenants.tax_regime`, `tax_settings`, `industry`).

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
