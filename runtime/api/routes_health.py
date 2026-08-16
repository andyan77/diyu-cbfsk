"""健康检查。

/healthz 只回答「进程还活着」，不碰数据库——它挂在存活探针上，
一旦让它依赖数据库，数据库抖动会把还能服务的进程一起重启掉。
/readyz 才回答「能接流量」，必须真的打一次库。
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from runtime.db import get_engine

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(response: Response) -> dict[str, str]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 —— 探针必须吞掉细节，不把连接串回给调用方
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "reason": type(exc).__name__}
    return {"status": "ready"}
