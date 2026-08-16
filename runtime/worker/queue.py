"""任务入队接口位。

`TaskQueue` 是**接口**，`InMemoryTaskQueue` 是骨架期唯一实现：进程内、不持久、不跨进程。
它被刻意做成一眼看得出「不能当生产用」的样子——一个假装持久化的内存队列，
比一个诚实的内存队列危险得多。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from runtime.domain.base import new_id


@dataclass(frozen=True)
class TaskEnvelope:
    """入队信封。tenant_id 是必填字段，不是可选上下文。

    异步任务是最容易丢租户的地方：请求上下文在入队那一刻就没了，
    如果信封里不带租户，Worker 侧只能靠载荷里碰巧有没有 tenant_id 来猜。
    """

    task_name: str
    tenant_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=new_id)
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class TaskQueue(Protocol):
    def put(self, envelope: TaskEnvelope) -> str: ...

    def get(self) -> TaskEnvelope | None: ...

    def depth(self) -> int: ...


class InMemoryTaskQueue:
    """骨架实现：进程重启即清空。BR1-EP03 换真实实现时只换这个类。"""

    def __init__(self) -> None:
        self._items: deque[TaskEnvelope] = deque()

    def put(self, envelope: TaskEnvelope) -> str:
        self._items.append(envelope)
        return envelope.task_id

    def get(self) -> TaskEnvelope | None:
        return self._items.popleft() if self._items else None

    def depth(self) -> int:
        return len(self._items)


_queue: TaskQueue = InMemoryTaskQueue()


def get_queue() -> TaskQueue:
    return _queue


def enqueue(task_name: str, tenant_id: str, payload: dict[str, Any] | None = None) -> str:
    """全仓唯一入队入口（EQ-1）。换实现时调用方一行不用改。"""
    if not tenant_id:
        raise ValueError("TENANT_REQUIRED: an enqueued task must carry its tenant")
    return get_queue().put(TaskEnvelope(task_name=task_name, tenant_id=tenant_id, payload=payload or {}))
