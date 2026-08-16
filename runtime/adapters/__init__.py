"""外部依赖 Adapter 接口位。BR0-EP01 不实调任何外部服务。"""

from runtime.adapters.object_storage import NullObjectStorage, ObjectStorage, StoredObject, get_object_storage

__all__ = ["NullObjectStorage", "ObjectStorage", "StoredObject", "get_object_storage"]
