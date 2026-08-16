"""Worker：进程骨架与 enqueue 接口位。

BR0-EP01 明确**不选型队列框架**：任何第三方队列/任务调度框架一律不引。
理由不是省事，而是队列选型要由真实的任务形态决定——重试语义、可见性超时、
有序性、死信处理，这些在 BR1-EP03 出现第一个真实异步任务之前全是猜。
先引一个框架，等于让骨架期的猜测锁死后面的真实需求。
"""

from runtime.worker.queue import InMemoryTaskQueue, TaskQueue, enqueue, get_queue

__all__ = ["InMemoryTaskQueue", "TaskQueue", "enqueue", "get_queue"]
