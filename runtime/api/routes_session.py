"""登录、登出与租户切换。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from runtime.api.deps import (
    SESSION_TENANT_KEY,
    SESSION_USER_KEY,
    CurrentUser,
    DbSession,
)
from runtime.api.schemas import LoginRequest, SelectTenantRequest, SessionOut, TenantOut, UserOut
from runtime.domain.models import Tenant, TenantMembership, User
from runtime.domain.security import verify_password

router = APIRouter(prefix="/api/session", tags=["session"])


def _session_out(db: DbSession, request: Request, user: User | None) -> SessionOut:
    if user is None:
        return SessionOut()
    tenant_id = request.session.get(SESSION_TENANT_KEY)
    active: TenantOut | None = None
    if tenant_id:
        row = db.execute(
            select(Tenant, TenantMembership.role)
            .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
            .where(Tenant.id == tenant_id, TenantMembership.user_id == user.id)
        ).one_or_none()
        if row is not None:
            tenant, role = row
            active = TenantOut(id=tenant.id, slug=tenant.slug, display_name=tenant.display_name, role=role)
    return SessionOut(
        user=UserOut(id=user.id, username=user.username, display_name=user.display_name),
        active_tenant=active,
    )


@router.post("", response_model=SessionOut)
def login(payload: LoginRequest, request: Request, db: DbSession) -> SessionOut:
    user = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    # 用户不存在与口令错误回同一个响应：分开回等于免费送一个用户名枚举接口。
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")
    request.session.clear()
    request.session[SESSION_USER_KEY] = user.id
    return _session_out(db, request, user)


@router.get("", response_model=SessionOut)
def read_session(request: Request, db: DbSession) -> SessionOut:
    user_id = request.session.get(SESSION_USER_KEY)
    user = db.get(User, user_id) if user_id else None
    return _session_out(db, request, user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> None:
    request.session.clear()


@router.put("/tenant", response_model=SessionOut)
def select_tenant(
    payload: SelectTenantRequest, request: Request, db: DbSession, user: CurrentUser
) -> SessionOut:
    """切换当前租户。

    这是全仓唯一一个接受 tenant_id 入参的端点，并且它做的不是「按参数取数据」，
    而是「校验成员关系后把租户固化进服务端会话」。校验失败即拒绝，会话不变。
    """
    membership = db.execute(
        select(TenantMembership).where(
            TenantMembership.tenant_id == payload.tenant_id, TenantMembership.user_id == user.id
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="NOT_A_TENANT_MEMBER")
    request.session[SESSION_TENANT_KEY] = payload.tenant_id
    return _session_out(db, request, user)
