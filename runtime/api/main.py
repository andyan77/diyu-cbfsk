"""FastAPI 应用装配。"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from runtime import __version__
from runtime.api import routes_health, routes_session, routes_workspace
from runtime.settings import DEV_SESSION_SEED, Settings, get_settings

# 前端构建产物挂载路径。与 web/vite.config.ts 的 base 必须一致——
# 两处各写各的会让刷新页面 404，而开发时用 dev server 又看不出来。
STATIC_MOUNT_PATH = "/app"
STATIC_DIST_DIR = Path(__file__).resolve().parents[2] / "web" / "dist"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    if settings.is_production and settings.session_secret == DEV_SESSION_SEED:
        # 生产用开发缺省种子意味着任何读过本仓的人都能伪造会话 Cookie。
        raise RuntimeError("SESSION_SECRET_NOT_CONFIGURED: production requires DIYU_CBFSK_SESSION_SECRET")

    app = FastAPI(title="笛语跨品牌服装搭配专家内核 · Runtime", version=__version__)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age_seconds,
        same_site="lax",
        https_only=settings.is_production,
    )
    app.include_router(routes_health.router)
    app.include_router(routes_session.router)
    app.include_router(routes_workspace.router)

    if STATIC_DIST_DIR.is_dir():
        app.mount(STATIC_MOUNT_PATH, StaticFiles(directory=STATIC_DIST_DIR, html=True), name="workbench")

    # 处理器定义在模块级、这里显式注册：写成 create_app 内的闭包时，
    # 装饰器是它唯一的引用点，静态检查看不到它被用过（reportUnusedFunction）。
    # 提到模块级顺带让它可以被单独调用与测试。
    app.get("/", include_in_schema=False)(index)

    return app


def index() -> RedirectResponse:
    """根路径重定向到工作台挂载点。"""
    return RedirectResponse(url=f"{STATIC_MOUNT_PATH}/")


app = create_app()
