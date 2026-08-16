"""Tenant / TenantMembership / Brand 根对象与首批客户数据表。

范围克制：本包只建立「租户安全根 + 一条能走通的最小业务链路（租户→品牌→草稿任务）」。
不建 RBAC 策略引擎、不建自助注册、不建收费面——见 PRD v0.3.2 §1.2。
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from runtime.domain.base import Base, TenantScopedMixin, TimestampMixin, new_id

TENANT_ROLES = ("OWNER", "REVIEWER", "OPERATOR")
TENANT_STATUSES = ("ACTIVE", "SUSPENDED")
DRAFT_TASK_STATUSES = ("DRAFT", "SUBMITTED", "ACCEPTED", "REJECTED")


def _in_clause(column: str, values: tuple[str, ...]) -> str:
    """把枚举写成 SQL CHECK 子句。常量只在上面定义一次，SQL 从它派生（EQ-4：无魔法常量）。"""
    joined = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({joined})"


class User(Base, TimestampMixin):
    """自然人身份。跨租户唯一，租户归属见 TenantMembership。"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # 口令摘要（scrypt）。明文口令任何时候都不落库、不进日志、不进响应体。
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")


class Tenant(Base, TimestampMixin):
    """租户根。主键即 tenant_id；本表不带 brand_id（执行合同 §四硬约束）。"""

    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(_in_clause("status", TENANT_STATUSES), name="status_enum"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")


class TenantMembership(Base, TenantScopedMixin, TimestampMixin):
    """人与租户的绑定。同一 (tenant, user) 只允许一条；本表不带 brand_id。

    「同租户跨品牌」是 PRD v0.3.2 的明确产品能力：成员授权到租户，不授权到品牌。
    一旦这里挂上 brand_id，跨品牌就退化成要为每个品牌重新邀请一次人。
    """

    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
        CheckConstraint(_in_clause("role", TENANT_ROLES), name="role_enum"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)


class TenantSettings(Base, TenantScopedMixin, TimestampMixin):
    """租户级设置。每租户至多一条；本表不带 brand_id。"""

    __tablename__ = "tenant_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_settings_tenant_id"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    default_locale: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-CN")


class Brand(Base, TenantScopedMixin, TimestampMixin):
    """品牌。品牌属于租户，不是全局对象——同名品牌在不同租户下互不可见。

    额外的 (tenant_id, id) 唯一约束是给下游品牌域表做复合外键用的：
    没有它，(tenant_id, brand_id) 复合外键在 PostgreSQL 里建不出来。
    """

    __tablename__ = "brands"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_brands_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_brands_tenant_id_id"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)


class DraftTask(Base, TenantScopedMixin, TimestampMixin):
    """草稿任务：本包唯一的品牌域业务表，用来把复合外键这条约束真正行使一次。

    复合外键 (tenant_id, brand_id) → brands(tenant_id, id) 让
    「A 租户的任务引用 B 租户的品牌」在数据库层面不可表达。
    只写单列外键 brand_id → brands.id 是不够的——那种模型下跨租户引用完全合法，
    全靠应用层每次记得加 WHERE tenant_id，漏一次就串租户。
    """

    __tablename__ = "draft_tasks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "brand_id"],
            ["brands.tenant_id", "brands.id"],
            name="fk_draft_tasks_tenant_brand",
            ondelete="RESTRICT",
        ),
        CheckConstraint(_in_clause("status", DRAFT_TASK_STATUSES), name="status_enum"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    brand_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
