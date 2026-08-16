"""Worker 进程骨架。

它现在只做一件事：起得来、轮询队列、收到停止信号后干净退出。
没有任何真实任务处理器——`HANDLERS` 是空的，且**不是**忘了填：
BR0-EP01 的验收对象是「进程骨架 + 接口位」，不是「能干活的 Worker」。
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from collections.abc import Callable
from types import FrameType

from runtime.worker.queue import TaskEnvelope, get_queue

LOGGER = logging.getLogger("runtime.worker")
POLL_INTERVAL_SECONDS = 1.0

# 任务名 → 处理器。BR1-EP03 才开始往这里注册真实处理器。
HANDLERS: dict[str, Callable[[TaskEnvelope], None]] = {}

_should_stop = False


def _request_stop(signum: int, frame: FrameType | None) -> None:
    global _should_stop
    del frame
    LOGGER.info("worker: received signal %s, draining", signum)
    _should_stop = True


def run_once() -> bool:
    """处理至多一个信封。返回是否真的处理了东西——供测试与自检使用。"""
    envelope = get_queue().get()
    if envelope is None:
        return False
    handler = HANDLERS.get(envelope.task_name)
    if handler is None:
        # 丢弃并留痕，而不是抛异常把整个进程带走。
        LOGGER.warning("worker: no handler for task %r, dropped", envelope.task_name)
        return True
    handler(envelope)
    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    LOGGER.info("worker: started with %d handler(s)", len(HANDLERS))
    while not _should_stop:
        if not run_once():
            time.sleep(POLL_INTERVAL_SECONDS)
    LOGGER.info("worker: stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
