"""租户安全根不变式（EP01-02 的确定性判据）。

三层各查各的，谁都不能替谁：
  1. 模型层  —— Base.metadata 里每张表都必须有租户归属
  2. 迁移层  —— 首个迁移**渲染出来的 SQL** 里真的写了 NOT NULL 与复合外键
  3. 活库层  —— 真的建出来了，且 app 角色是 NOBYPASSRLS

只查第 1 层是不够的：模型对了而迁移写漏，生产库里就是没有那条约束。
只查第 3 层也不够：活库不可达时整组用例会 skip，判据就静默消失了。
"""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, text

from runtime.domain.base import BRAND_SCOPED_TABLES, NO_BRAND_ID_TABLES, TENANT_ROOT_TABLES, Base
from runtime.domain.models import Brand, DraftTask, Tenant, TenantMembership, TenantSettings, User
from tests.conftest import OFFLINE_URL, TEST_MIGRATOR_URL_ENV, requires_live_db

# 引用一次，保证 metadata 完整（导入即注册）。
_MODELS = (Brand, DraftTask, Tenant, TenantMembership, TenantSettings, User)

APP_ROLE = "cbfsk_app"
MIGRATOR_ROLE = "cbfsk_migrator"


def _expected_tenant_scoped() -> set[str]:
    """所有既不是租户根、也不是 alembic 自身的表，一律要求带 tenant_id。"""
    return set(Base.metadata.tables) - set(TENANT_ROOT_TABLES)


# ---------------------------------------------------------------- 1. 模型层


def test_every_table_is_either_tenant_root_or_tenant_scoped() -> None:
    for name, table in Base.metadata.tables.items():
        if name in TENANT_ROOT_TABLES:
            assert TENANT_ROOT_TABLES[name].strip(), f"{name} 列在租户根白名单里却没写理由"
            continue
        column = table.columns.get("tenant_id")
        assert column is not None, f"{name} 既不在租户根白名单里，也没有 tenant_id"
        assert column.nullable is False, f"{name}.tenant_id 可空——数据库允许存在无归属的客户数据行"


def test_tenant_scoped_set_is_not_empty() -> None:
    """覆盖面下限：白名单一旦被写成「全表都是租户根」，上一条用例会一片绿。"""
    assert len(_expected_tenant_scoped()) >= 4


def test_tenant_and_membership_and_settings_carry_no_brand_id() -> None:
    for name in NO_BRAND_ID_TABLES:
        table = Base.metadata.tables[name]
        assert "brand_id" not in table.columns, f"{name} 不得带 brand_id（同租户跨品牌会退化成按品牌重新邀请）"


def test_brand_scoped_tables_use_composite_foreign_key() -> None:
    for name in BRAND_SCOPED_TABLES:
        table = Base.metadata.tables[name]
        composite = [
            fk for fk in table.foreign_key_constraints if {c.name for c in fk.columns} == {"tenant_id", "brand_id"}
        ]
        assert composite, f"{name} 缺少 (tenant_id, brand_id) 复合外键——跨租户引用在库层面仍然合法"
        referred = {element.target_fullname for element in composite[0].elements}
        assert referred == {"brands.tenant_id", "brands.id"}, f"{name} 的复合外键指向了 {referred}"


# ---------------------------------------------------------------- 2. 迁移层


@pytest.fixture(scope="module")
def rendered_migration_sql(tmp_path_factory: pytest.TempPathFactory) -> str:
    """离线渲染首个迁移的 SQL。不连库，因此在任何环境都跑得动。"""
    del tmp_path_factory
    import os

    previous = os.environ.get(TEST_MIGRATOR_URL_ENV)
    os.environ["DIYU_CBFSK_MIGRATOR_DATABASE_URL"] = OFFLINE_URL
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            command.upgrade(Config("alembic.ini"), "head", sql=True)
    finally:
        if previous is None:
            os.environ.pop(TEST_MIGRATOR_URL_ENV, None)
    return buffer.getvalue()


def test_rendered_migration_declares_tenant_id_not_null(rendered_migration_sql: str) -> None:
    for name in _expected_tenant_scoped():
        block = re.search(rf"CREATE TABLE {name} \((.*?)\n\);", rendered_migration_sql, re.S)
        assert block, f"渲染出的 SQL 里没有 CREATE TABLE {name}"
        assert re.search(r"tenant_id VARCHAR\(32\) NOT NULL", block.group(1)), (
            f"{name} 的建表语句里 tenant_id 不是 NOT NULL"
        )


def test_rendered_migration_declares_composite_brand_foreign_key(rendered_migration_sql: str) -> None:
    normalized = " ".join(rendered_migration_sql.split())
    assert "FOREIGN KEY(tenant_id, brand_id) REFERENCES brands (tenant_id, id)" in normalized


def test_rendered_migration_grants_no_ddl_to_app_role(rendered_migration_sql: str) -> None:
    """app 角色只能拿到 DML。授出 CREATE/ALTER/DROP 等于让长驻进程能改结构。"""
    grants = re.findall(rf"GRANT ([A-Z, ]+) ON [^;]*TO {APP_ROLE}", rendered_migration_sql)
    for grant in grants:
        privileges = {p.strip() for p in grant.split(",")}
        assert privileges <= {"SELECT", "INSERT", "UPDATE", "DELETE", "USAGE"}, f"越权授予：{privileges}"


# ---------------------------------------------------------------- 3. 活库层


@requires_live_db
def test_live_schema_enforces_tenant_root(migrator_engine: Engine) -> None:
    inspector = inspect(migrator_engine)
    tables = set(inspector.get_table_names())
    assert _expected_tenant_scoped() <= tables, "迁移没有把全部租户域表建出来"
    for name in _expected_tenant_scoped():
        columns = {c["name"]: c for c in inspector.get_columns(name)}
        assert "tenant_id" in columns, f"活库里 {name} 没有 tenant_id"
        assert columns["tenant_id"]["nullable"] is False, f"活库里 {name}.tenant_id 可空"


@requires_live_db
def test_live_schema_has_composite_brand_foreign_key(migrator_engine: Engine) -> None:
    inspector = inspect(migrator_engine)
    composite = [
        fk
        for fk in inspector.get_foreign_keys("draft_tasks")
        if set(fk["constrained_columns"]) == {"tenant_id", "brand_id"}
    ]
    assert composite, "活库里 draft_tasks 没有 (tenant_id, brand_id) 复合外键"
    assert composite[0]["referred_table"] == "brands"
    assert set(composite[0]["referred_columns"]) == {"tenant_id", "id"}


@requires_live_db
def test_live_roles_are_separated_and_app_cannot_bypass_rls(migrator_engine: Engine) -> None:
    with migrator_engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT rolname, rolbypassrls, rolsuper, rolcreatedb, rolcreaterole "
                "FROM pg_roles WHERE rolname IN (:app, :migrator)"
            ),
            {"app": APP_ROLE, "migrator": MIGRATOR_ROLE},
        ).mappings().all()
    by_name = {row["rolname"]: row for row in rows}
    assert set(by_name) == {APP_ROLE, MIGRATOR_ROLE}, f"角色未分离，实际存在 {sorted(by_name)}"
    app = by_name[APP_ROLE]
    assert app["rolbypassrls"] is False, "app 角色可以绕过 RLS"
    assert app["rolsuper"] is False
    assert app["rolcreatedb"] is False
    assert app["rolcreaterole"] is False
