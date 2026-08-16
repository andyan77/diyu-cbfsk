"""租户、品牌与草稿任务端点。

除「创建租户」外，所有读写都以 TenantId 依赖为准；查询一律带 tenant_id 过滤。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from runtime.api.deps import SESSION_TENANT_KEY, CurrentUser, DbSession, TenantId
from runtime.api.schemas import (
    BrandOut,
    CreateBrandRequest,
    CreateDraftTaskRequest,
    CreateTenantRequest,
    DraftTaskOut,
    TenantOut,
)
from runtime.domain.models import Brand, DraftTask, Tenant, TenantMembership, TenantSettings

router = APIRouter(prefix="/api", tags=["workspace"])


@router.get("/tenants", response_model=list[TenantOut])
def list_my_tenants(db: DbSession, user: CurrentUser) -> list[TenantOut]:
    rows = db.execute(
        select(Tenant, TenantMembership.role)
        .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
        .where(TenantMembership.user_id == user.id)
        .order_by(Tenant.created_at)
    ).all()
    return [
        TenantOut(id=tenant.id, slug=tenant.slug, display_name=tenant.display_name, role=role)
        for tenant, role in rows
    ]


@router.post("/tenants", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: CreateTenantRequest, request: Request, db: DbSession, user: CurrentUser
) -> TenantOut:
    """由已登录的 Founder/Operator 创建租户并成为 OWNER。

    这不是自助注册：调用方必须先有账号，而账号只能由 `python -m runtime.bootstrap`
    在服务端创建——没有任何匿名可达的开户入口（PRD v0.3.2 §1.2）。
    """
    if db.execute(select(Tenant).where(Tenant.slug == payload.slug)).scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TENANT_SLUG_TAKEN")
    tenant = Tenant(slug=payload.slug, display_name=payload.display_name)
    db.add(tenant)
    db.flush()
    db.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role="OWNER"))
    db.add(TenantSettings(tenant_id=tenant.id))
    db.flush()
    request.session[SESSION_TENANT_KEY] = tenant.id
    return TenantOut(id=tenant.id, slug=tenant.slug, display_name=tenant.display_name, role="OWNER")


@router.get("/brands", response_model=list[BrandOut])
def list_brands(db: DbSession, tenant_id: TenantId) -> list[BrandOut]:
    brands = db.execute(
        select(Brand).where(Brand.tenant_id == tenant_id).order_by(Brand.created_at)
    ).scalars().all()
    return [BrandOut(id=b.id, code=b.code, display_name=b.display_name) for b in brands]


@router.post("/brands", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(payload: CreateBrandRequest, db: DbSession, tenant_id: TenantId) -> BrandOut:
    existing = db.execute(
        select(Brand).where(Brand.tenant_id == tenant_id, Brand.code == payload.code)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="BRAND_CODE_TAKEN")
    brand = Brand(tenant_id=tenant_id, code=payload.code, display_name=payload.display_name)
    db.add(brand)
    db.flush()
    return BrandOut(id=brand.id, code=brand.code, display_name=brand.display_name)


@router.get("/draft-tasks", response_model=list[DraftTaskOut])
def list_draft_tasks(db: DbSession, tenant_id: TenantId) -> list[DraftTaskOut]:
    tasks = db.execute(
        select(DraftTask).where(DraftTask.tenant_id == tenant_id).order_by(DraftTask.created_at)
    ).scalars().all()
    return [
        DraftTaskOut(id=t.id, brand_id=t.brand_id, title=t.title, status=t.status) for t in tasks
    ]


@router.post("/draft-tasks", response_model=DraftTaskOut, status_code=status.HTTP_201_CREATED)
def create_draft_task(
    payload: CreateDraftTaskRequest, db: DbSession, tenant_id: TenantId
) -> DraftTaskOut:
    """品牌必须属于当前租户。

    这里的显式校验与数据库的复合外键是两道**互不替代**的关卡：
    应用层给出可读错误，数据库层保证即使应用层被绕过也写不进去。
    """
    brand = db.execute(
        select(Brand).where(Brand.tenant_id == tenant_id, Brand.id == payload.brand_id)
    ).scalar_one_or_none()
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BRAND_NOT_IN_TENANT")
    task = DraftTask(tenant_id=tenant_id, brand_id=brand.id, title=payload.title)
    db.add(task)
    db.flush()
    return DraftTaskOut(id=task.id, brand_id=task.brand_id, title=task.title, status=task.status)
