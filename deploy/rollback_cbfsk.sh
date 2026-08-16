#!/usr/bin/env bash
# 支线回滚。两种模式：
#   stop              停掉支线容器，保留库与配置（共享主机上的其他应用完全不受影响）
#   <40 位 git sha>   切回某个已在本机构建过的镜像
#
# 本脚本永远不 DROP 数据库、不删桶、不删 /etc/diyu-cbfsk——回滚是回代码版本，
# 不是抹掉数据。要销毁资源必须人工执行，且是独立决定。
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must run as root on the ECS host." >&2
  exit 1
fi

target="${1:?Usage: rollback_cbfsk.sh <40-character-git-sha|stop>}"
compose_file="/opt/diyu-cbfsk/source/deploy/docker-compose.staging.yml"
config_dir="/etc/diyu-cbfsk"
export COMPOSE_PROJECT_NAME="diyu-cbfsk"

if [[ "$target" == "stop" ]]; then
  export DIYU_CBFSK_IMAGE_REF="unused-for-stop"
  docker compose -f "$compose_file" stop api worker >/dev/null 2>&1 || true
  printf 'Branch stack stopped; database, bucket and configuration were retained.\n'
  exit 0
fi

if [[ ! "$target" =~ ^[0-9a-f]{40}$ ]]; then
  echo "A full lowercase Git SHA or the literal stop is required." >&2
  exit 1
fi

app_port="$(sed -n 's/^DIYU_CBFSK_APP_PORT=//p' "$config_dir/app.env")"
export DIYU_CBFSK_IMAGE_REF="diyu-cbfsk-runtime:$target"
docker image inspect "$DIYU_CBFSK_IMAGE_REF" >/dev/null
docker compose -f "$compose_file" up -d --no-build api worker

for _ in $(seq 1 30); do
  if curl --fail --silent "http://127.0.0.1:$app_port/readyz" >/dev/null; then
    printf 'Branch staging rolled back to %s and is ready.\n' "$target"
    exit 0
  fi
  sleep 2
done

echo "Rollback target failed its readiness check." >&2
exit 1
