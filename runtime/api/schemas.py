"""请求与响应模型。

注意除租户切换请求外，这里**没有**任何字段承载租户标识：租户上下文一律由服务端
从会话取，不接受请求方传入。把租户标识放进业务请求体，等于把隔离边界交给调用方自觉。

全文件里租户标识**字段声明**恰好一处（SelectTenantRequest），CI 的 boundaries 作业
按这个数目判定——多出一处就是多了一个可由调用方指定租户的入口。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class SelectTenantRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=32)


class CreateTenantRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    display_name: str = Field(min_length=1, max_length=128)


class CreateBrandRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    display_name: str = Field(min_length=1, max_length=128)


class CreateDraftTaskRequest(BaseModel):
    brand_id: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: str
    username: str
    display_name: str


class TenantOut(BaseModel):
    id: str
    slug: str
    display_name: str
    role: str


class BrandOut(BaseModel):
    id: str
    code: str
    display_name: str


class DraftTaskOut(BaseModel):
    id: str
    brand_id: str
    title: str
    status: str


class SessionOut(BaseModel):
    user: UserOut | None = None
    active_tenant: TenantOut | None = None
