"""alembic 运行环境。

迁移用 **migrator** 角色，应用运行时用 **app** 角色——两者的连接串是不同的环境变量，
不共用。缺 migrator 串时**不回退**到 app 串：回退会让迁移悄悄以应用角色执行，
角色分离就此形同虚设。
"""

from __future__ import annotations

import os

from alembic import context
from runtime.domain.base import Base
from runtime.domain.models import Brand, DraftTask, Tenant, TenantMembership, TenantSettings, User
from sqlalchemy import engine_from_config, pool

# 导入模型是为了让 Base.metadata 完整。显式引用一次，免得 linter 判为未使用而删掉。
_MODELS = (Brand, DraftTask, Tenant, TenantMembership, TenantSettings, User)

MIGRATOR_URL_ENV = "DIYU_CBFSK_MIGRATOR_DATABASE_URL"

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    url = os.environ.get(MIGRATOR_URL_ENV, "").strip()
    if not url:
        raise RuntimeError(f"MIGRATOR_URL_MISSING: set {MIGRATOR_URL_ENV} before running alembic")
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
