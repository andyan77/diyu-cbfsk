"""租户安全根的**单一定义处**（EQ-1）。

PRD v0.3.2 §10.5：在建第一张客户数据表时就必须具备正确的租户安全根。这条要求
一旦当场不做，事后补 `tenant_id` 需要回填全部历史行、且无法恢复行到底属于哪个租户。
所以本文件不是文档，而是被 `tests/test_tenant_root_invariants.py` 逐表行使的可执行合同。

三张表的分类是**穷举且互斥**的：`Base.metadata` 里的每一张表都必须落在
`TENANT_ROOT_TABLES` 里（并写明为什么它不带 `tenant_id`），否则一律要求
`tenant_id NOT NULL`。新增一张表却忘了挂租户根，测试会当场判失败——
而不是等到生产库里已经有了没有租户归属的行。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 命名约定：约束名由 SQLAlchemy 统一生成，alembic autogenerate 与手写迁移才不会各起各的名字。
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# 不带 tenant_id 的表：必须逐张写明理由。这是白名单，不是例外的兜底口袋。
TENANT_ROOT_TABLES: dict[str, str] = {
    "tenants": "本表是租户根自身，主键 tenants.id 即 tenant_id；再挂一列 tenant_id 是自指冗余。",
    "users": (
        "自然人身份跨租户唯一：同一个人可同时是 A 租户的 Owner 与 B 租户的 Reviewer。"
        "租户归属由 tenant_memberships 承载并强制，身份表本身不携带租户，"
        "否则同一个人要在每个租户各存一份口令与身份，反而制造跨租户可关联的重复身份。"
    ),
    "alembic_version": "alembic 自身的版本表，不是客户数据表。",
}

# 品牌域表：必须以复合外键 (tenant_id, brand_id) 指向 brands，
# 让「A 租户的任务引用 B 租户的品牌」在数据库层面直接不可表达，而不是靠应用层记得过滤。
BRAND_SCOPED_TABLES: frozenset[str] = frozenset({"draft_tasks"})

# 明令不得出现 brand_id 的表（执行合同 §四硬约束）。
NO_BRAND_ID_TABLES: frozenset[str] = frozenset({"tenants", "tenant_memberships", "tenant_settings"})


class Base(DeclarativeBase):
    """全库唯一的 declarative base。"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def new_id() -> str:
    """主键生成：UUID4 十六进制。

    不用自增整数——自增主键会把「本租户创建了多少行」泄露给任何拿到一个 id 的租户。
    """
    return uuid.uuid4().hex


class TimestampMixin:
    """创建/更新时间。服务端时钟，不接受客户端传入。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(UTC)
    )


class TenantScopedMixin:
    """所有客户数据表的租户根。

    `nullable=False` 不是风格选择：可空的 tenant_id 意味着数据库允许存在
    「不属于任何租户」的客户数据行，而那种行在跨租户查询里既不会被本租户过滤掉，
    也不会被任何租户认领。
    """

    tenant_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
