"""Тестовая база: перед сессией тестов схема пересоздаётся миграциями.

Тесты работают с базой из DATABASE_URL (см. README: docker compose up -d db redis).
Данные в тестах — только обезличенные.
"""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield
