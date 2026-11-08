"""Подключение к PostgreSQL.

Платформа многоклиентская: каждая клиентская таблица содержит tenant_id
и защищена row-level security. С данными клиента работаем только через
tenant_session(): она выставляет app.tenant_id на время транзакции,
а политики RLS (спринт 1, задача 2) читают это значение.
"""
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def tenant_session(tenant_id: UUID) -> Iterator[Session]:
    """Сессия, в которой видны только данные одного клиента."""
    with SessionLocal() as session, session.begin():
        session.execute(
            text("SELECT set_config('app.tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        yield session
