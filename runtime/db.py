"""数据库会话。应用运行时只用 app 角色，迁移只用 migrator 角色。

两个角色不是仪式：app 角色若能建表改表，一次应用侧注入就等于一次结构变更；
migrator 角色若被长驻进程持有，同样的权限会一直挂在网络可达的位置上。
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from runtime.settings import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().app_database_url, pool_pre_ping=True, future=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _session_factory


def session_scope() -> Iterator[Session]:
    """FastAPI 依赖：每请求一个会话，异常回滚。"""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
