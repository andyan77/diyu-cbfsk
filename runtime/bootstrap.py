"""一次性初始化：创建首个操作员账号。

没有任何匿名可达的开户入口（PRD v0.3.2 §1.2「不做客户自助注册」），
所以首个账号只能在服务端由本模块创建。取值全部来自环境变量，不落仓、不进日志。

用法：DIYU_CBFSK_INITIAL_OPS_USERNAME=... DIYU_CBFSK_INITIAL_OPS_PASSWORD=... \
      python -m runtime.bootstrap
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import select

from runtime.db import get_session_factory
from runtime.domain.models import User
from runtime.domain.security import hash_password

USERNAME_ENV = "DIYU_CBFSK_INITIAL_OPS_USERNAME"
PASSWORD_ENV = "DIYU_CBFSK_INITIAL_OPS_PASSWORD"


def main() -> int:
    username = os.environ.get(USERNAME_ENV, "").strip()
    secret_value = os.environ.get(PASSWORD_ENV, "")
    if not username or not secret_value:
        print(f"SKIP bootstrap: {USERNAME_ENV} / {PASSWORD_ENV} not set", file=sys.stderr)
        return 0

    session = get_session_factory()()
    try:
        existing = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if existing is not None:
            # 幂等：compose 每次起都会跑一遍，重复执行不得覆盖已有账号的口令。
            print(f"SKIP bootstrap: user {username!r} already exists", file=sys.stderr)
            return 0
        session.add(User(username=username, password_hash=hash_password(secret_value), display_name=username))
        session.commit()
        print(f"OK bootstrap: created user {username!r}", file=sys.stderr)
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
