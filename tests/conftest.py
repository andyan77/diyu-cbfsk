"""pytest 公共夹具。

活库地址来自 DIYU_CBFSK_TEST_MIGRATOR_URL / DIYU_CBFSK_TEST_APP_URL。
没有活库时，需要活库的用例 **skip**——写成 skip 而不是让它假通过：
一条永远绿的用例比没有这条用例更危险。
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text

TEST_MIGRATOR_URL_ENV = "DIYU_CBFSK_TEST_MIGRATOR_URL"
TEST_APP_URL_ENV = "DIYU_CBFSK_TEST_APP_URL"

# 离线渲染 SQL 用的占位地址。alembic --sql 模式不会连接它。
OFFLINE_URL = "postgresql+psycopg://offline@localhost:5432/offline"


def live_migrator_url() -> str | None:
    return os.environ.get(TEST_MIGRATOR_URL_ENV) or None


def live_app_url() -> str | None:
    return os.environ.get(TEST_APP_URL_ENV) or None


requires_live_db = pytest.mark.skipif(
    live_migrator_url() is None,
    reason=f"live database not configured; set {TEST_MIGRATOR_URL_ENV}",
)


@pytest.fixture(scope="session")
def migrator_engine() -> Iterator[Engine]:
    url = live_migrator_url()
    if url is None:
        pytest.skip(f"set {TEST_MIGRATOR_URL_ENV}")
    engine = create_engine(url, future=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield engine
    engine.dispose()
