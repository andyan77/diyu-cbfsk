"""/healthz 与 /readyz 的真实用例。

/healthz 必须在数据库不可达时仍然 200——它是存活探针。
如果它跟着数据库一起红，Kubernetes 之外的任何编排（本包用的是 compose + systemd）
都会把还能服务的进程反复重启，把一次数据库抖动放大成一次全站不可用。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from runtime.api.main import create_app
from runtime.settings import Settings


def _client() -> TestClient:
    settings = Settings(
        runtime_mode="test",
        app_database_url="postgresql+psycopg://nobody@127.0.0.1:1/does-not-exist",
    )
    return TestClient(create_app(settings))


def test_healthz_is_ok_without_database() -> None:
    with _client() as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_unavailable_when_database_is_unreachable() -> None:
    """就绪探针必须真的打库。不打库的 readyz 只是第二个 healthz。"""
    with _client() as client:
        response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_unauthenticated_workspace_access_is_rejected() -> None:
    with _client() as client:
        assert client.get("/api/tenants").status_code == 401
        assert client.get("/api/brands").status_code == 401
