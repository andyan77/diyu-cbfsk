# ECS Staging 运行手册 · 笛语跨品牌服装搭配专家内核

> 适用范围：BR0-EP01 运行时骨架在**共享 ECS 主机**上的冷部署、验证、回滚与销毁。
> 本手册不覆盖公网暴露——支线 Staging 只监听回环，是否对外由独立决定。

## 0. 这台机器上还住着别人

共享主机上已有另一套**正在对外服务**的应用，以及它依赖的共享基础设施容器。
本手册的每一条命令都遵守同一条纪律：

- 支线只**新增**资源，从不修改、停止、删除任何非 `diyu-cbfsk-` 前缀的容器、库、桶或配置目录。
- 支线**只读依赖**共享的 PostgreSQL 与 MinIO 容器：连接它们、在里面新建自己的库与桶，
  但不重启它们、不改它们的配置、不动它们的既有对象。
- 部署前后各验一次邻居应用的 `/health/ready`、`/health/live`、`/status`，
  三项都必须是 200。任一非 200 立即回滚支线侧改动。

## 1. 命名空间（不得偏离）

| 资源 | 支线取值 |
|---|---|
| PostgreSQL 库 | `diyu_cbfsk` |
| 数据库角色 | `cbfsk_migrator` / `cbfsk_app` |
| 对象存储桶 | `diyu-cbfsk-materials` |
| 配置目录 | `/etc/diyu-cbfsk` |
| 应用目录 | `/opt/diyu-cbfsk` |
| 备份目录 | `/var/backups/diyu-cbfsk` |
| 容器名前缀 | `diyu-cbfsk-` |
| 应用端口 | 从 18000 起顺延，占用则 +1（由 provision 现算并写入 `app.env`） |

端口是**算出来的**，不是写死的：共享主机上已有服务占着 18000，写死会直接抢端口。

## 2. 冷部署

```bash
# 2.1 同步运行时源码子集（只传运行时需要的目录，不传治理文档与产品真源）
rsync -az --delete \
  --include='runtime/***' --include='alembic/***' --include='web/***' \
  --include='ops/***' --include='deploy/***' \
  --include='pyproject.toml' --include='uv.lock' --include='alembic.ini' \
  --include='Dockerfile' --include='.dockerignore' \
  --exclude='*' \
  ./ root@<host>:/opt/diyu-cbfsk/source/

# 2.2 一次性 provision（建库、建角色、建桶、写 /etc/diyu-cbfsk、算端口）
/opt/diyu-cbfsk/source/deploy/provision_cbfsk.sh

# 2.3 构建候选镜像（标签用完整 40 位 Git SHA，不用 latest）
docker build -t "diyu-cbfsk-runtime:<40-hex-sha>" /opt/diyu-cbfsk/source

# 2.4 部署：迁移 → 初始账号 → 起 api/worker → 健康检查 → 邻居复验
/opt/diyu-cbfsk/source/deploy/deploy_cbfsk.sh <40-hex-sha>
```

`provision_cbfsk.sh` 在 `/etc/diyu-cbfsk` 已存在配置时**拒绝执行**，不覆盖。
需要重新 provision 必须人工先确认旧配置可以丢，这是独立决定。

## 3. 初始账号

`bootstrap.env` 里的初始口令由 provision 现场随机生成。**跑完 bootstrap 后立即删除该文件**：

```bash
shred -u /etc/diyu-cbfsk/bootstrap.env
```

它是一次性初始化材料，不是运行时配置；留在盘上等于把一个管理员口令长期挂在文件系统里。

## 4. 验证

本手册一律用变量指代共享基础设施容器与邻居端点，不写它们的实际名字——
那是部署环境的事实，不是支线仓的内容：

```bash
export DIYU_CBFSK_POSTGRES_CONTAINER=<共享 PostgreSQL 容器名>
export DIYU_CBFSK_MINIO_CONTAINER=<共享 MinIO 容器名>
export DIYU_CBFSK_NEIGHBOUR_PROBE=<邻居应用健康探针基址>
```

```bash
port="$(sed -n 's/^DIYU_CBFSK_APP_PORT=//p' /etc/diyu-cbfsk/app.env)"
curl -sS "http://127.0.0.1:$port/healthz"    # {"status":"ok"}
curl -sS "http://127.0.0.1:$port/readyz"     # {"status":"ready"}

# 租户安全根的活库证据
docker exec "$DIYU_CBFSK_POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d diyu_cbfsk -c \
  "SELECT table_name, is_nullable FROM information_schema.columns
    WHERE column_name='tenant_id' AND table_schema='public' ORDER BY table_name;"
docker exec "$DIYU_CBFSK_POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d diyu_cbfsk -c \
  "SELECT rolname, rolbypassrls FROM pg_roles WHERE rolname LIKE 'cbfsk%';"
```

## 5. 回滚

```bash
/opt/diyu-cbfsk/source/deploy/rollback_cbfsk.sh stop              # 停服，保留数据
/opt/diyu-cbfsk/source/deploy/rollback_cbfsk.sh <40-hex-sha>      # 切回旧镜像
```

回滚**不**删库、不删桶、不删配置。销毁资源是另一件事，见第 6 节，必须人工单独执行。

## 6. 销毁（人工，独立决定）

```bash
docker rm -f diyu-cbfsk-api diyu-cbfsk-worker
docker exec -i "$DIYU_CBFSK_POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c 'DROP DATABASE diyu_cbfsk' -c 'DROP ROLE cbfsk_app' -c 'DROP ROLE cbfsk_migrator'
rm -rf /etc/diyu-cbfsk /opt/diyu-cbfsk
```

对象存储桶不在此列：桶里可能有素材，删桶必须先确认内容，不能跟着一条销毁命令一起走。

## 7. 备份

BR0-EP01 只交付骨架，尚无客户数据，因此**未**安装定时备份 timer。
第一条真实客户数据进库之前，备份必须先就位——这条在 BR1 的退出门上，
不是可以边跑边补的运维细节。
