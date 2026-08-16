"""跨租户引用必须被**数据库**拒绝，而不只是被应用层拒绝。

这条用例故意绕开所有应用代码，直接用 SQL 插入一条「A 租户的任务引用 B 租户的品牌」。
如果它插进去了，说明隔离只存在于 Python 里——那么任何一处忘记加 WHERE tenant_id
的查询、任何一条手工修数据的 SQL，都能把两个客户的数据搅在一起。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from tests.conftest import requires_live_db


def _hex() -> str:
    return uuid.uuid4().hex


@requires_live_db
def test_database_rejects_task_referencing_another_tenants_brand(migrator_engine: Engine) -> None:
    tenant_a, tenant_b = _hex(), _hex()
    brand_b, task_id = _hex(), _hex()

    with migrator_engine.begin() as connection:
        for tenant_id, slug in ((tenant_a, f"a-{tenant_a[:8]}"), (tenant_b, f"b-{tenant_b[:8]}")):
            connection.execute(
                text(
                    "INSERT INTO tenants (id, slug, display_name, status) "
                    "VALUES (:id, :slug, :name, 'ACTIVE')"
                ),
                {"id": tenant_id, "slug": slug, "name": slug},
            )
        connection.execute(
            text(
                "INSERT INTO brands (id, tenant_id, code, display_name) "
                "VALUES (:id, :tenant_id, :code, :name)"
            ),
            {"id": brand_b, "tenant_id": tenant_b, "code": f"C{brand_b[:8]}", "name": "B 租户的品牌"},
        )

    try:
        with pytest.raises(IntegrityError), migrator_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO draft_tasks (id, tenant_id, brand_id, title, status) "
                    "VALUES (:id, :tenant_id, :brand_id, :title, 'DRAFT')"
                ),
                {"id": task_id, "tenant_id": tenant_a, "brand_id": brand_b, "title": "越界任务"},
            )
    finally:
        with migrator_engine.begin() as connection:
            connection.execute(text("DELETE FROM draft_tasks WHERE id = :id"), {"id": task_id})
            connection.execute(text("DELETE FROM brands WHERE id = :id"), {"id": brand_b})
            connection.execute(
                text("DELETE FROM tenants WHERE id IN (:a, :b)"), {"a": tenant_a, "b": tenant_b}
            )


@requires_live_db
def test_database_rejects_task_without_tenant(migrator_engine: Engine) -> None:
    with pytest.raises(IntegrityError), migrator_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO draft_tasks (id, tenant_id, brand_id, title, status) "
                "VALUES (:id, NULL, :brand_id, :title, 'DRAFT')"
            ),
            {"id": _hex(), "brand_id": _hex(), "title": "无租户任务"},
        )
