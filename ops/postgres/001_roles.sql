-- 本地 Compose 的角色初始化。ECS 上由 deploy/provision_cbfsk.sh 做同样的事，
-- 但口令由 openssl rand 现场生成，不用本文件的开发取值。
--
-- 两个角色的分工：
--   cbfsk_migrator —— 只在迁移期使用，拥有库、可改结构
--   cbfsk_app      —— 长驻应用使用，NOBYPASSRLS，且拿不到 DDL 权限
-- NOBYPASSRLS 是显式写的：PostgreSQL 的默认已经是 NOBYPASSRLS，
-- 但「默认如此」和「合同要求如此」是两件事——写出来，才有东西可被校验。

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cbfsk_migrator') THEN
        CREATE ROLE cbfsk_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS
            PASSWORD 'cbfsk.migrator.local';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cbfsk_app') THEN
        CREATE ROLE cbfsk_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT
            PASSWORD 'cbfsk.app.local';
    END IF;
END
$$;

ALTER DATABASE diyu_cbfsk OWNER TO cbfsk_migrator;
GRANT CONNECT ON DATABASE diyu_cbfsk TO cbfsk_app;
