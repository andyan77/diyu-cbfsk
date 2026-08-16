#!/usr/bin/env bash
# 支线 Staging 部署。只动 diyu-cbfsk-* 容器与 /opt/diyu-cbfsk。
#
# 与共享主机上其他应用的关系：**只读依赖**它们的 PostgreSQL 与 MinIO 容器，
# 不重启、不改配置、不改它们的 Nginx server 块。部署前后各验一次它们的健康，
# 任一非 200 立即回滚支线侧改动。
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must run as root on the ECS host." >&2
  exit 1
fi

sha="${1:?Usage: deploy_cbfsk.sh <40-character-git-sha>}"
if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "A full lowercase Git SHA is required." >&2
  exit 1
fi

app_dir="/opt/diyu-cbfsk"
source_dir="$app_dir/source"
compose_file="$source_dir/deploy/docker-compose.staging.yml"
config_dir="/etc/diyu-cbfsk"
# 邻居应用的健康探针地址同样由部署方给定，仓内不写默认值——
# 那是别人的对外端点，不属于支线仓的内容。
neighbour_probe="${DIYU_CBFSK_NEIGHBOUR_PROBE:?set DIYU_CBFSK_NEIGHBOUR_PROBE}"

test -f "$config_dir/app.env"
test -f "$config_dir/migrator.env"
test -f "$compose_file"

app_port="$(sed -n 's/^DIYU_CBFSK_APP_PORT=//p' "$config_dir/app.env")"
[[ -n "$app_port" ]] || { echo "DIYU_CBFSK_APP_PORT missing from app.env" >&2; exit 1; }

probe_neighbour() {
  local label="$1" failed=0 path code
  for path in /health/ready /health/live /status; do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$neighbour_probe$path" || true)"
    printf '%s neighbour %s -> %s\n' "$label" "$path" "$code"
    [[ "$code" == "200" ]] || failed=1
  done
  return "$failed"
}

probe_neighbour predeploy || { echo "Neighbour application is not healthy before deploy; aborting." >&2; exit 1; }

export DIYU_CBFSK_IMAGE_REF="diyu-cbfsk-runtime:$sha"
export COMPOSE_PROJECT_NAME="diyu-cbfsk"

docker image inspect "$DIYU_CBFSK_IMAGE_REF" >/dev/null

docker compose -f "$compose_file" --profile maintenance run --rm migrate </dev/null
if [[ -f "$config_dir/bootstrap.env" ]]; then
  docker compose -f "$compose_file" --profile maintenance run --rm bootstrap </dev/null
fi
docker compose -f "$compose_file" up -d --no-build api worker

for _ in $(seq 1 30); do
  if curl --fail --silent "http://127.0.0.1:$app_port/healthz" >/dev/null; then
    if ! curl --fail --silent "http://127.0.0.1:$app_port/readyz" >/dev/null; then
      echo "Branch service is live but not ready; leaving it up for inspection." >&2
      exit 1
    fi
    if ! probe_neighbour postdeploy; then
      echo "Neighbour application degraded after deploy; rolling the branch stack back." >&2
      "$source_dir/deploy/rollback_cbfsk.sh" stop
      exit 1
    fi
    printf 'Branch staging %s is healthy on 127.0.0.1:%s; neighbour unaffected.\n' "$sha" "$app_port"
    exit 0
  fi
  sleep 2
done

echo "Branch staging failed its health check; stopping the branch stack." >&2
"$source_dir/deploy/rollback_cbfsk.sh" stop
exit 1
