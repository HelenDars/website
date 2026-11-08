"""Основная схема NORDIS (раздел 3 ТЗ) и разделение клиентов.

Каждая клиентская таблица содержит tenant_id и защищена row-level security:
строка видна, только если tenant_id совпадает с app.tenant_id текущей
транзакции (его выставляет app.db.tenant_session).

Роль nordis_app — роль, под которой работает приложение с данными клиента.
У неё нет права обходить RLS. Владелец схемы (роль миграций) RLS обходит:
он нужен для админки NORDIS (создание клиентов, общий справочник).

Денежные суммы — numeric(18,2): тенге с тиынами, чтобы сверка с ОПиУ
клиента сходилась до тенге без ошибок округления.

Revision ID: 0001
Revises:
Create Date: 2026-11-08
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

APP_ROLE = "nordis_app"
MONEY = "numeric(18,2)"

# Общие поля загружаемых данных: источник, ID записи в источнике
# (ключ идемпотентной загрузки), загрузка, время обновления.
SRC = """
    source          text not null default 'manual',
    source_id       text,
    ingest_run_id   bigint references ingest_runs(id) on delete set null,
    updated_at      timestamptz not null default now()
"""
TENANT = "tenant_id uuid not null references tenants(id) on delete cascade"

TABLES: list[tuple[str, str]] = [
    # ---------- 3.1 Служебные ----------
    ("users", f"""
        id          uuid primary key default gen_random_uuid(),
        {TENANT},
        full_name   text not null,
        phone       text,
        email       text,
        telegram_id text,
        role        text not null references roles(code),
        is_active   boolean not null default true,
        created_at  timestamptz not null default now()
    """),
    ("connections", f"""
        id               uuid primary key default gen_random_uuid(),
        {TENANT},
        source_type      text not null,
        name             text not null,
        secret_encrypted bytea,
        settings         jsonb not null default '{{}}',
        status           text not null default 'new'
                         check (status in ('new','ok','error','disabled')),
        last_success_at  timestamptz,
        last_error       text,
        created_at       timestamptz not null default now()
    """),
    ("ingest_runs", f"""
        id             bigint generated always as identity primary key,
        {TENANT},
        connection_id  uuid references connections(id) on delete set null,
        source_type    text not null,
        file_name      text,
        started_at     timestamptz not null default now(),
        finished_at    timestamptz,
        status         text not null default 'running'
                       check (status in ('running','ok','error')),
        records_in     integer not null default 0,
        records_loaded integer not null default 0,
        error          text
    """),
    ("audit_log", f"""
        id          bigint generated always as identity primary key,
        {TENANT},
        actor_type  text not null check (actor_type in ('user','ai','system')),
        actor_id    text,
        action      text not null,
        object_type text,
        object_id   text,
        details     jsonb not null default '{{}}',
        at          timestamptz not null default now()
    """),
    # ---------- 3.2 Сырые данные ----------
    # Одна таблица на все источники (вместо raw_<источник>): тип источника
    # и сущность — в колонках, данные — как пришли, в jsonb.
    ("raw_records", f"""
        id            bigint generated always as identity primary key,
        {TENANT},
        ingest_run_id bigint not null references ingest_runs(id) on delete cascade,
        source_type   text not null,
        entity        text not null,
        source_id     text,
        payload       jsonb not null,
        received_at   timestamptz not null default now()
    """),
    # ---------- Справочник статей и сопоставление (3.4) ----------
    ("account_mapping", f"""
        id          bigint generated always as identity primary key,
        {TENANT},
        source      text not null,
        source_name text not null,
        account_id  bigint not null references pnl_accounts(id),
        created_at  timestamptz not null default now(),
        unique (tenant_id, source, source_name)
    """),
    # ---------- 3.3 Основные ----------
    ("pnl_entries", f"""
        id            bigint generated always as identity primary key,
        {TENANT},
        period_month  date not null check (extract(day from period_month) = 1),
        entry_date    date,
        account_id    bigint not null references pnl_accounts(id),
        branch        text,
        channel       text,
        amount        {MONEY} not null,
        source_name   text,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("cash_transactions", f"""
        id             bigint generated always as identity primary key,
        {TENANT},
        op_date        date not null,
        account_name   text not null,
        direction      text not null check (direction in ('in','out')),
        amount         {MONEY} not null,
        counterparty   text,
        purpose        text,
        pnl_account_id bigint references pnl_accounts(id),
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("cash_balances", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        as_of        date not null,
        account_name text not null,
        balance      {MONEY} not null,
        {SRC},
        unique (tenant_id, source, as_of, account_name)
    """),
    ("products", f"""
        id              bigint generated always as identity primary key,
        {TENANT},
        sku             text not null,
        name            text not null,
        category        text,
        price           {MONEY},
        unit_cost       {MONEY},
        cost_changed_on date,
        {SRC},
        unique (tenant_id, sku)
    """),
    ("orders", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        ordered_at   timestamptz not null,
        channel      text not null,
        branch       text,
        amount       {MONEY} not null,
        status       text not null default 'new',
        closed_by    text check (closed_by in ('human','ai_seller')),
        customer_ref text,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("order_items", f"""
        id        bigint generated always as identity primary key,
        {TENANT},
        order_id  bigint not null references orders(id) on delete cascade,
        sku       text not null,
        qty       numeric(14,3) not null,
        price     {MONEY} not null,
        unit_cost {MONEY}
    """),
    # Агрегированные продажи по дням (когда у клиента нет заказов поштучно,
    # а есть дневной отчёт по филиалам и каналам).
    ("sales_daily", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        sale_date    date not null,
        branch       text not null default '',
        channel      text not null default '',
        revenue      {MONEY} not null,
        orders_count integer,
        leads        numeric(12,2),
        inquiries    integer,
        {SRC},
        unique (tenant_id, source, sale_date, branch, channel)
    """),
    ("stock", f"""
        id        bigint generated always as identity primary key,
        {TENANT},
        as_of     date not null,
        sku       text not null,
        warehouse text not null default '',
        qty       numeric(14,3) not null,
        {SRC},
        unique (tenant_id, source, as_of, sku, warehouse)
    """),
    ("leads", f"""
        id          bigint generated always as identity primary key,
        {TENANT},
        created_at  timestamptz not null,
        channel     text,
        campaign    text,
        creative    text,
        contact_ref text,
        status      text,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("deals", f"""
        id               bigint generated always as identity primary key,
        {TENANT},
        stage            text,
        amount           {MONEY},
        manager          text,
        opened_at        timestamptz,
        closed_at        timestamptz,
        proposal_sent_at timestamptz,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("dialogs", f"""
        id          bigint generated always as identity primary key,
        {TENANT},
        channel     text not null,
        contact_ref text,
        handled_by  text check (handled_by in ('human','ai')),
        started_at  timestamptz not null,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("messages", f"""
        id               bigint generated always as identity primary key,
        {TENANT},
        dialog_id        bigint not null references dialogs(id) on delete cascade,
        sent_at          timestamptz not null,
        sender           text not null check (sender in ('customer','human','ai')),
        body             text,
        response_seconds integer
    """),
    ("ad_spend", f"""
        id          bigint generated always as identity primary key,
        {TENANT},
        spend_date  date not null,
        platform    text,
        ad_account  text,
        specialist  text,
        direction   text,
        branch      text,
        channel     text,
        campaign    text,
        creative    text,
        spend_usd   numeric(14,2),
        fx_rate     numeric(12,4),
        spend       {MONEY} not null,
        impressions bigint,
        clicks      bigint,
        leads       numeric(12,2),
        sales       integer,
        ad_revenue  {MONEY},
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("contracts", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        counterparty text not null,
        kind         text not null
                     check (kind in ('customer','supplier','rent','loan','other')),
        amount       {MONEY},
        starts_on    date,
        ends_on      date,
        file_ref     text,
        confirmed_by uuid references users(id),
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("payment_schedule", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        due_date     date not null,
        counterparty text,
        amount       {MONEY} not null,
        direction    text not null check (direction in ('in','out')),
        status       text not null default 'planned'
                     check (status in ('planned','paid','overdue','cancelled')),
        contract_id  bigint references contracts(id) on delete set null,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("payroll", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        period_month date not null,
        employee     text,
        position     text,
        department   text,
        salary       {MONEY} not null default 0,
        bonus        {MONEY} not null default 0,
        taxes        {MONEY} not null default 0,
        {SRC},
        unique (tenant_id, source, source_id)
    """),
    ("tasks", f"""
        id          bigint generated always as identity primary key,
        {TENANT},
        title       text not null,
        assignee_id uuid references users(id),
        due_at      timestamptz,
        origin      text not null check (origin in ('ai','human')),
        agent       text,
        status      text not null default 'open'
                    check (status in ('open','done','cancelled')),
        created_at  timestamptz not null default now()
    """),
    ("alerts", f"""
        id         bigint generated always as identity primary key,
        {TENANT},
        kind       text not null,
        severity   text not null check (severity in ('info','warning','critical')),
        body       text not null,
        data       jsonb not null default '{{}}',
        status     text not null default 'open'
                   check (status in ('open','acknowledged','resolved')),
        created_at timestamptz not null default now()
    """),
    ("personal_events", f"""
        id         bigint generated always as identity primary key,
        {TENANT},
        user_id    uuid references users(id) on delete cascade,
        title      text not null,
        event_date date not null,
        remind_at  timestamptz
    """),
    # Правила решений ИИ (раздел 5): auto / propose / owner_only с лимитами.
    ("decision_rules", f"""
        id         bigint generated always as identity primary key,
        {TENANT},
        agent      text not null,
        action     text not null,
        level      text not null check (level in ('auto','propose','owner_only')),
        limits     jsonb not null default '{{}}',
        updated_by uuid references users(id),
        updated_at timestamptz not null default now(),
        unique (tenant_id, agent, action)
    """),
    ("ai_actions", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        agent        text not null,
        action       text not null,
        rule_id      bigint references decision_rules(id),
        rule_level   text check (rule_level in ('auto','propose','owner_only')),
        input        jsonb not null default '{{}}',
        result       jsonb not null default '{{}}',
        confirmed_by uuid references users(id),
        at           timestamptz not null default now()
    """),
    ("billing_ai_sales", f"""
        id           bigint generated always as identity primary key,
        {TENANT},
        order_id     bigint not null references orders(id),
        period_month date not null,
        amount       {MONEY} not null,
        fee          {MONEY} not null,
        unique (tenant_id, order_id)
    """),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} NOLOGIN NOBYPASSRLS;
            END IF;
        END $$;
    """)
    # Владелец схемы может переключаться в роль приложения (SET ROLE).
    op.execute(f"GRANT {APP_ROLE} TO current_user")

    # Текущий клиент; пусто или не задано -> NULL -> не видно ничего.
    op.execute("""
        CREATE FUNCTION current_tenant_id() RETURNS uuid
        LANGUAGE sql STABLE AS
        $$ SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid $$
    """)

    op.execute("""
        CREATE TABLE tenants (
            id               uuid primary key default gen_random_uuid(),
            name             text not null,
            industry         text,
            legal_form       text,
            package          text not null default 'trial'
                             check (package in ('trial','lite','business','premium')),
            trial_started_on date,
            trial_ends_on    date,
            tax_regime       text,
            tax_settings     jsonb not null default '{}',
            timezone         text not null default 'Asia/Almaty',
            created_at       timestamptz not null default now()
        )
    """)
    op.execute("""
        CREATE TABLE roles (
            code text primary key,
            name text not null
        )
    """)
    op.execute("""
        INSERT INTO roles (code, name) VALUES
            ('owner', 'Владелец'),
            ('rop', 'Руководитель отдела продаж'),
            ('targetologist', 'Таргетолог'),
            ('manager', 'Менеджер'),
            ('accountant', 'Бухгалтер')
    """)
    # Справочник статей ОПиУ: tenant_id IS NULL — общая статья платформы,
    # иначе — собственная статья клиента. Раздел определяет место в расчёте
    # прибыли (см. app/metrics).
    op.execute(f"""
        CREATE TABLE pnl_accounts (
            id          bigint generated always as identity primary key,
            tenant_id   uuid references tenants(id) on delete cascade,
            code        text not null,
            name        text not null,
            parent_code text,
            section     text not null check (section in (
                            'revenue','cogs','variable','marketing','fixed',
                            'interest','depreciation','tax')),
            industry    text,
            sort_order  integer not null default 0,
            is_active   boolean not null default true
        )
    """)
    op.execute("CREATE UNIQUE INDEX pnl_accounts_global_code ON pnl_accounts (code) WHERE tenant_id IS NULL")
    op.execute("CREATE UNIQUE INDEX pnl_accounts_tenant_code ON pnl_accounts (tenant_id, code) WHERE tenant_id IS NOT NULL")

    for name, columns in TABLES:
        op.execute(f"CREATE TABLE {name} ({columns})")
        op.execute(f"CREATE INDEX {name}_tenant_idx ON {name} (tenant_id)")

    # ---------- Row-level security ----------
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON tenants USING (id = current_tenant_id())")

    op.execute("ALTER TABLE pnl_accounts ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON pnl_accounts
        USING (tenant_id IS NULL OR tenant_id = current_tenant_id())
        WITH CHECK (tenant_id = current_tenant_id())
    """)

    for name, _ in TABLES:
        op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {name}
            USING (tenant_id = current_tenant_id())
            WITH CHECK (tenant_id = current_tenant_id())
        """)

    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
    op.execute(f"REVOKE INSERT, UPDATE, DELETE ON tenants, roles FROM {APP_ROLE}")
    op.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}")
    op.execute(f"REVOKE ALL ON alembic_version FROM {APP_ROLE}")


def downgrade() -> None:
    for name, _ in reversed(TABLES):
        op.execute(f"DROP TABLE IF EXISTS {name} CASCADE")
    op.execute("DROP TABLE IF EXISTS pnl_accounts, roles, tenants CASCADE")
    op.execute("DROP FUNCTION IF EXISTS current_tenant_id()")
    op.execute(f"REVOKE ALL ON SCHEMA public FROM {APP_ROLE}")
