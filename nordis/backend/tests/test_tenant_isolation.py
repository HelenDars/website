"""Данные одного клиента не видны и недоступны другому (раздел 6 ТЗ)."""
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db import admin_session, engine, tenant_session


def _create_tenant(name: str) -> UUID:
    with admin_session() as s:
        return s.execute(
            text("INSERT INTO tenants (name, tax_regime) VALUES (:n, 'simplified') RETURNING id"),
            {"n": name},
        ).scalar_one()


@pytest.fixture(scope="module")
def two_tenants():
    a, b = _create_tenant("Клиент А"), _create_tenant("Клиент Б")
    with admin_session() as s:
        acc = s.execute(text(
            "INSERT INTO pnl_accounts (code, name, section) "
            "VALUES ('test.revenue', 'Выручка (тест)', 'revenue') RETURNING id"
        )).scalar_one()
        for tid, amount in ((a, 1000), (b, 2000)):
            s.execute(
                text("INSERT INTO pnl_entries (tenant_id, period_month, account_id, amount, source, source_id) "
                     "VALUES (:t, '2026-01-01', :acc, :amt, 'test', 'r1')"),
                {"t": tid, "acc": acc, "amt": amount},
            )
    return a, b, acc


def test_tenant_sees_only_own_rows(two_tenants):
    a, b, _ = two_tenants
    with tenant_session(a) as s:
        rows = s.execute(text("SELECT tenant_id, amount FROM pnl_entries")).all()
    assert [(r.tenant_id, int(r.amount)) for r in rows] == [(a, 1000)]

    with tenant_session(b) as s:
        rows = s.execute(text("SELECT tenant_id, amount FROM pnl_entries")).all()
    assert [(r.tenant_id, int(r.amount)) for r in rows] == [(b, 2000)]


def test_tenant_sees_only_own_tenant_card(two_tenants):
    a, _, _ = two_tenants
    with tenant_session(a) as s:
        ids = s.execute(text("SELECT id FROM tenants")).scalars().all()
    assert ids == [a]


def test_cannot_write_into_other_tenant(two_tenants):
    a, b, acc = two_tenants
    with pytest.raises(DBAPIError, match="row-level security"):
        with tenant_session(a) as s:
            s.execute(
                text("INSERT INTO pnl_entries (tenant_id, period_month, account_id, amount) "
                     "VALUES (:t, '2026-02-01', :acc, 1)"),
                {"t": b, "acc": acc},
            )


def test_cannot_update_other_tenant_rows(two_tenants):
    a, _, _ = two_tenants
    with tenant_session(a) as s:
        s.execute(text("UPDATE pnl_entries SET amount = 0"))
    with admin_session() as s:
        amounts = sorted(int(x) for x in s.execute(text("SELECT amount FROM pnl_entries")).scalars())
    assert amounts == [0, 2000]  # тронута только строка клиента А
    with admin_session() as s:
        s.execute(text("UPDATE pnl_entries SET amount = 1000 WHERE tenant_id = :a"), {"a": a})


def test_global_accounts_visible_but_not_writable(two_tenants):
    a, _, _ = two_tenants
    with tenant_session(a) as s:
        codes = s.execute(text("SELECT code FROM pnl_accounts")).scalars().all()
    assert "test.revenue" in codes
    with pytest.raises(DBAPIError, match="row-level security"):
        with tenant_session(a) as s:
            s.execute(text(
                "INSERT INTO pnl_accounts (tenant_id, code, name, section) "
                "VALUES (NULL, 'hack', 'x', 'revenue')"
            ))


def test_no_tenant_set_sees_nothing(two_tenants):
    with engine.connect() as conn, conn.begin():
        conn.execute(text("SET LOCAL ROLE nordis_app"))
        assert conn.execute(text("SELECT count(*) FROM pnl_entries")).scalar_one() == 0
        assert conn.execute(text("SELECT count(*) FROM tenants")).scalar_one() == 0


def test_every_tenant_table_has_rls():
    """Новая таблица с tenant_id без RLS — ошибка, тест её поймает."""
    with admin_session() as s:
        unprotected = s.execute(text("""
            SELECT c.relname FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
            WHERE c.relkind = 'r'
              AND (c.relname = 'tenants' OR EXISTS (
                  SELECT 1 FROM pg_attribute a
                  WHERE a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped))
              AND (NOT c.relrowsecurity
                   OR NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid))
        """)).scalars().all()
    assert unprotected == []
