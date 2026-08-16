#!/usr/bin/env bash
# 支线（笛语跨品牌服装搭配专家内核）在共享 ECS 上的一次性 provision。
#
# 结构参考共享主机上既有应用的 provision 流程，但**所有标识符都换成支线独占取值**：
# 库、角色、桶、配置目录、应用目录、备份目录、容器前缀、端口，一个都不复用。
# 原脚本不能原样跑——它硬编了另一套应用的容器名与目录，跑一次就会把两套应用搅在一起。
#
# 本脚本只**新增**资源。它从不 DROP、不 ALTER 既有对象、不改任何非本前缀的容器。
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
  echo "This script must run as root on the ECS host." >&2
  exit 1
fi

postgres_container="${DIYU_CBFSK_POSTGRES_CONTAINER:-diyu-infra-postgres-1}"
minio_container="${DIYU_CBFSK_MINIO_CONTAINER:-diyu-infra-minio-1}"

config_dir="/etc/diyu-cbfsk"
app_dir="/opt/diyu-cbfsk"
backup_dir="/var/backups/diyu-cbfsk"
app_env="$config_dir/app.env"
migrator_env="$config_dir/migrator.env"
bootstrap_env="$config_dir/bootstrap.env"

database_name="diyu_cbfsk"
migrator_role="cbfsk_migrator"
app_role="cbfsk_app"
bucket_name="diyu-cbfsk-materials"

# 端口从 18000 起顺延，被占用则 +1。共享主机上已有服务占着 18000，
# 硬写 18000 会在启动时和别人抢端口——所以这里现算，不写死。
base_port="${DIYU_CBFSK_BASE_PORT:-18000}"
app_port="$base_port"
while ss -ltn "( sport = :$app_port )" | tail -n +2 | grep -q .; do
  app_port=$((app_port + 1))
done

if [[ -e "$app_env" || -e "$migrator_env" || -e "$bootstrap_env" ]]; then
  echo "Refusing to overwrite existing configuration in $config_dir." >&2
  exit 1
fi

# 依赖的共享基础设施必须已经在跑。这里只 inspect，不启动、不重启、不修改。
docker inspect "$postgres_container" >/dev/null
docker inspect "$minio_container" >/dev/null

install -d -m 700 "$config_dir" "$app_dir" "$backup_dir"

app_db_pw="$(openssl rand -hex 32)"
mig_db_pw="$(openssl rand -hex 32)"
session_secret="$(openssl rand -hex 48)"
s3_access_key="cbfsk-$(openssl rand -hex 8)"
s3_secret_key="$(openssl rand -base64 36 | tr -d '\n')"
ops_pw="$(openssl rand -base64 30 | tr -d '\n')"

existing_roles="$(docker exec "$postgres_container" sh -lc \
  "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -Atc \"SELECT string_agg(rolname, ',' ORDER BY rolname) FROM pg_roles WHERE rolname IN ('$migrator_role', '$app_role')\"")"
if [[ -n "$existing_roles" ]]; then
  echo "Roles $existing_roles already exist; refusing to reuse or re-key them." >&2
  exit 1
fi

docker exec -i "$postgres_container" sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' <<SQL >/dev/null
CREATE ROLE ${migrator_role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD '${mig_db_pw}';
CREATE ROLE ${app_role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT PASSWORD '${app_db_pw}';
SELECT format('CREATE DATABASE %I OWNER %I', '${database_name}', '${migrator_role}')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '${database_name}')\gexec
GRANT CONNECT ON DATABASE ${database_name} TO ${app_role};
SQL

docker exec -i "$minio_container" sh -ec '
  IFS= read -r access_key
  IFS= read -r secret_key
  IFS= read -r bucket
  if [ -n "${MINIO_ROOT_USER_FILE:-}" ] && [ -r "$MINIO_ROOT_USER_FILE" ]; then MINIO_ROOT_USER=$(cat "$MINIO_ROOT_USER_FILE"); fi
  if [ -n "${MINIO_ROOT_PASSWORD_FILE:-}" ] && [ -r "$MINIO_ROOT_PASSWORD_FILE" ]; then MINIO_ROOT_PASSWORD=$(cat "$MINIO_ROOT_PASSWORD_FILE"); fi
  mc alias set cbfsk http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  mc mb --ignore-existing "cbfsk/$bucket" >/dev/null
  printf "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:ListBucket\"],\"Resource\":[\"arn:aws:s3:::%s\"]},{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\"],\"Resource\":[\"arn:aws:s3:::%s/*\"]}]}" "$bucket" "$bucket" > /tmp/cbfsk-policy.json
  mc admin policy create cbfsk "$bucket" /tmp/cbfsk-policy.json >/dev/null
  mc admin user add cbfsk "$access_key" "$secret_key" >/dev/null
  mc admin policy attach cbfsk "$bucket" --user "$access_key" >/dev/null
  rm -f /tmp/cbfsk-policy.json
' <<EOF
${s3_access_key}
${s3_secret_key}
${bucket_name}
EOF

umask 077
cat >"$app_env" <<EOF
DIYU_CBFSK_RUNTIME_MODE=production
DIYU_CBFSK_APP_PORT=$app_port
DIYU_CBFSK_APP_DATABASE_URL=postgresql+psycopg://${app_role}:$app_db_pw@127.0.0.1:5432/${database_name}
DIYU_CBFSK_SESSION_SECRET=$session_secret
DIYU_CBFSK_S3_ENDPOINT_URL=http://127.0.0.1:9000
DIYU_CBFSK_S3_BUCKET=${bucket_name}
DIYU_CBFSK_S3_ACCESS_KEY_ID=$s3_access_key
DIYU_CBFSK_S3_SECRET_ACCESS_KEY=$s3_secret_key
DIYU_CBFSK_PUBLIC_URL=http://127.0.0.1:$app_port
EOF

# migrator 串单独放一个文件：长驻的 api / worker 只 env_file 挂 app.env，
# 拿不到能改结构的连接串。
cat >"$migrator_env" <<EOF
DIYU_CBFSK_MIGRATOR_DATABASE_URL=postgresql+psycopg://${migrator_role}:$mig_db_pw@127.0.0.1:5432/${database_name}
EOF

# 一次性初始化用。跑完即删——见 runbook。
cat >"$bootstrap_env" <<EOF
DIYU_CBFSK_INITIAL_OPS_USERNAME=cbfsk-ops
DIYU_CBFSK_INITIAL_OPS_PASSWORD=$ops_pw
EOF

chmod 600 "$app_env" "$migrator_env" "$bootstrap_env"
printf 'Provisioned isolated database %s, roles %s/%s, bucket %s, config %s, port %s.\n' \
  "$database_name" "$migrator_role" "$app_role" "$bucket_name" "$config_dir" "$app_port"
