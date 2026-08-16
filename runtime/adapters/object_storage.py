"""对象存储 Adapter 接口位。

只定义接口与一个**明确拒绝**的空实现。不引 boto3、不建连接、不读凭据。
空实现抛异常而不是静默成功：静默成功的存储 Adapter 会让上层以为素材已经存下，
等到真的要取的时候才发现从来没写过。

对象键强制以 `tenants/<tenant_id>/` 开头——租户隔离在存储侧同样是根，
不是取对象时才加的过滤条件。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

TENANT_KEY_PREFIX = "tenants"


@dataclass(frozen=True)
class StoredObject:
    key: str
    size_bytes: int
    content_type: str


def tenant_object_key(tenant_id: str, relative_key: str) -> str:
    """全仓唯一的对象键构造处（EQ-1）。"""
    if not tenant_id:
        raise ValueError("TENANT_REQUIRED: object key must be tenant-rooted")
    return f"{TENANT_KEY_PREFIX}/{tenant_id}/{relative_key.lstrip('/')}"


class ObjectStorage(Protocol):
    def put_object(self, tenant_id: str, relative_key: str, data: bytes, content_type: str) -> StoredObject: ...

    def presigned_get_url(self, tenant_id: str, relative_key: str, expires_seconds: int) -> str: ...


class NullObjectStorage:
    """未配置对象存储时的实现：一律拒绝，并说明缺什么。"""

    def put_object(self, tenant_id: str, relative_key: str, data: bytes, content_type: str) -> StoredObject:
        del data, content_type
        raise RuntimeError(
            f"OBJECT_STORAGE_NOT_CONFIGURED: refusing to accept {tenant_object_key(tenant_id, relative_key)}"
        )

    def presigned_get_url(self, tenant_id: str, relative_key: str, expires_seconds: int) -> str:
        del expires_seconds
        raise RuntimeError(
            f"OBJECT_STORAGE_NOT_CONFIGURED: refusing to sign {tenant_object_key(tenant_id, relative_key)}"
        )


_storage: ObjectStorage = NullObjectStorage()


def get_object_storage() -> ObjectStorage:
    return _storage
