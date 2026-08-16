"""Worker 骨架与 Adapter 接口位的行为。"""

from __future__ import annotations

import pytest
from runtime.adapters.object_storage import NullObjectStorage, tenant_object_key
from runtime.worker.main import HANDLERS, run_once
from runtime.worker.queue import InMemoryTaskQueue, TaskEnvelope, enqueue


def test_enqueue_refuses_a_task_without_tenant() -> None:
    """异步任务丢租户是最难查的串租户来源——入队处直接拒。"""
    with pytest.raises(ValueError, match="TENANT_REQUIRED"):
        enqueue("noop", tenant_id="")


def test_enqueue_returns_task_id_and_queue_depth_grows() -> None:
    queue = InMemoryTaskQueue()
    assert queue.depth() == 0
    task_id = queue.put(TaskEnvelope(task_name="noop", tenant_id="t1"))
    assert queue.depth() == 1
    assert queue.get() is not None and queue.depth() == 0
    assert isinstance(task_id, str) and len(task_id) == 32


def test_worker_has_no_handlers_yet() -> None:
    """BR0-EP01 交付的是骨架，不是能干活的 Worker。这条用例把该事实钉住，
    免得后续包在没有队列选型的情况下悄悄往里塞真实处理器。"""
    assert HANDLERS == {}


def test_worker_run_once_returns_false_on_empty_queue() -> None:
    assert run_once() is False


def test_object_storage_key_is_tenant_rooted() -> None:
    assert tenant_object_key("t1", "/materials/a.png") == "tenants/t1/materials/a.png"
    with pytest.raises(ValueError, match="TENANT_REQUIRED"):
        tenant_object_key("", "a.png")


def test_null_object_storage_refuses_loudly() -> None:
    """未配置就静默成功的存储 Adapter，会让上层以为素材已经存下。"""
    storage = NullObjectStorage()
    with pytest.raises(RuntimeError, match="OBJECT_STORAGE_NOT_CONFIGURED"):
        storage.put_object("t1", "a.png", b"x", "image/png")
    with pytest.raises(RuntimeError, match="OBJECT_STORAGE_NOT_CONFIGURED"):
        storage.presigned_get_url("t1", "a.png", 60)
