"""0001 tenant root —— 首个迁移：租户安全根与最小业务链路。

本迁移是 PRD v0.3.2 §10.5 的落地：第一张客户数据表建出来的那一刻，
`tenant_id NOT NULL` 与品牌域复合外键就必须在场。
这不是可以留到 BR1 再补的整改项——补的时候历史行已经无法判定归属。

Revision ID: 0001_tenant_root
Revises:
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_tenant_root"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 应用角色。建角色是 provision 的事（migrator 是 NOCREATEROLE），
# 迁移只负责把表权限授给它——所以角色不存在时跳过授权而不是报错。
APP_ROLE = "cbfsk_app"

TENANT_SCOPED_TABLES = ("tenant_memberships", "tenant_settings", "brands", "draft_tasks")
ALL_TABLES = ("tenants", "users", *TENANT_SCOPED_TABLES)


def _timestamps() -> tuple[sa.Column[sa.DateTime], sa.Column[sa.DateTime]]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED')", name="ck_tenants_status_enum"),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("role IN ('OWNER', 'REVIEWER', 'OPERATOR')", name="ck_tenant_memberships_role_enum"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_tenant_memberships_tenant_id_tenants", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_memberships"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"])
    op.create_index("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"])

    op.create_table(
        "tenant_settings",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("default_locale", sa.String(length=16), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_tenant_settings_tenant_id_tenants", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_settings"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_settings_tenant_id"),
    )
    op.create_index("ix_tenant_settings_tenant_id", "tenant_settings", ["tenant_id"])

    op.create_table(
        "brands",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_brands_tenant_id_tenants", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_brands"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_brands_tenant_code"),
        # 复合外键的被引用侧必须唯一，否则 draft_tasks 的 (tenant_id, brand_id) 建不出来。
        sa.UniqueConstraint("tenant_id", "id", name="uq_brands_tenant_id_id"),
    )
    op.create_index("ix_brands_tenant_id", "brands", ["tenant_id"])

    op.create_table(
        "draft_tasks",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("brand_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'ACCEPTED', 'REJECTED')", name="ck_draft_tasks_status_enum"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_draft_tasks_tenant_id_tenants", ondelete="RESTRICT"
        ),
        # 跨租户引用在这里被数据库直接拒掉，不依赖应用层记得加过滤条件。
        sa.ForeignKeyConstraint(
            ["tenant_id", "brand_id"],
            ["brands.tenant_id", "brands.id"],
            name="fk_draft_tasks_tenant_brand",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_draft_tasks"),
    )
    op.create_index("ix_draft_tasks_tenant_id", "draft_tasks", ["tenant_id"])
    op.create_index("ix_draft_tasks_brand_id", "draft_tasks", ["brand_id"])

    _grant_app_role()


def _grant_app_role() -> None:
    """把 DML 权限授给 app 角色，但**不授** DDL。

    app 角色拿不到 CREATE/ALTER/DROP：长驻进程一旦被注入，能改数据是一回事，
    能改结构是另一回事。角色不存在（例如 CI 里用超级用户跑迁移）时跳过。
    """
    table_list = ", ".join(ALL_TABLES)
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                    EXECUTE 'GRANT USAGE ON SCHEMA public TO {APP_ROLE}';
                    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON {table_list} TO {APP_ROLE}';
                END IF;
            END
            $$;
            """
        )
    )


def downgrade() -> None:
    op.drop_table("draft_tasks")
    op.drop_table("brands")
    op.drop_table("tenant_settings")
    op.drop_table("tenant_memberships")
    op.drop_table("users")
    op.drop_table("tenants")
