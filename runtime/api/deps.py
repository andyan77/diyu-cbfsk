"""会话与租户上下文依赖。

单一定义处（EQ-1）：全仓只有 `current_tenant_id()` 一处能产出「当前租户」。
任何端点想知道自己在哪个租户下工作，都必须经过它；它只读服务端会话，
不看查询参数、不看请求体、不看请求头。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from runtime.db import session_scope
from runtime.domain.models import TenantMembership, User

SESSION_USER_KEY = "user_id"
SESSION_TENANT_KEY = "active_tenant_id"

DbSession = Annotated[Session, Depends(session_scope)]


def current_user(request: Request, db: DbSession) -> User:
    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def current_tenant_id(request: Request, db: DbSession, user: CurrentUser) -> str:
    """当前租户。会话里没有、或成员关系已被撤销，一律拒绝——不回退到「第一个租户」。

    回退到某个默认租户是最容易被忽略的串租户来源：会话状态丢失时，
    请求会静默落到一个用户碰巧有权限的租户上，而调用方以为自己还在原来那个。
    """
    raw = request.session.get(SESSION_TENANT_KEY)
    # 会话内容来自签名 Cookie，类型上是 Any——显式收窄成 str，别把 Any 顺着依赖链传下去。
    tenant_id = raw if isinstance(raw, str) else ""
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NO_ACTIVE_TENANT")
    membership = db.execute(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == user.id
        )
    ).scalar_one_or_none()
    if membership is None:
        request.session.pop(SESSION_TENANT_KEY, None)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TENANT_MEMBERSHIP_REVOKED")
    return tenant_id


TenantId = Annotated[str, Depends(current_tenant_id)]
