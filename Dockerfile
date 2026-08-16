# 多阶段：Node 24 构建工作台前端，Python 3.13 运行后端。
# 前端产物直接进运行镜像，运行时不需要 Node，也不需要单独的静态服务器。

FROM node:24-bookworm-slim AS web
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim-bookworm AS runtime
# UV_PROJECT_ENVIRONMENT 必须显式指向 /opt/venv：不设它，uv sync 会往
# /srv/app/.venv 装，而 PATH 指的是 /opt/venv/bin —— 结果是 import 得到（cwd 在
# sys.path 上），控制台脚本却全不在，alembic 直接 command not found。
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /srv/app

RUN pip install --no-cache-dir uv==0.9.7

# --no-install-project：本镜像不把 runtime 打成 wheel 装进去，直接用 /srv/app 上的源码
# （WORKDIR 在 sys.path 上）。少一次构建步骤，也让容器里跑的就是仓里那份代码。
COPY pyproject.toml uv.lock ./
RUN uv venv /opt/venv && uv sync --frozen --no-dev --no-install-project

COPY runtime/ ./runtime/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY --from=web /build/dist ./web/dist

EXPOSE 18000
CMD ["uvicorn", "runtime.api.main:app", "--host", "0.0.0.0", "--port", "18000"]
