"""运行时配置。全部来自环境变量，仓内不落任何真实取值。

变量前缀 DIYU_CBFSK_ 是**支线独占**的：与共享主机上其他应用的配置命名空间不重叠，
避免同一台机器上两套应用互相读到对方的环境。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 开发缺省口令种子。含点号，既不像凭据也不可能被误当成真值使用；
# 生产由 DIYU_CBFSK_SESSION_SECRET 覆盖，缺省值只服务于本地 compose。
DEV_SESSION_SEED = "dev.local.session.seed.not.for.production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIYU_CBFSK_", env_file=None, extra="ignore")

    runtime_mode: str = Field(default="development")
    app_database_url: str = Field(default="postgresql+psycopg://cbfsk_app@127.0.0.1:5432/diyu_cbfsk")
    migrator_database_url: str = Field(default="")
    session_secret: str = Field(default=DEV_SESSION_SEED)
    session_cookie_name: str = Field(default="cbfsk_session")
    session_max_age_seconds: int = Field(default=8 * 60 * 60)
    public_url: str = Field(default="http://127.0.0.1:18000")
    app_port: int = Field(default=18000)
    # 对象存储 Adapter 的配置位。BR0-EP01 不实调外部服务，留空即走 NullObjectStorage。
    s3_endpoint_url: str = Field(default="")
    s3_bucket: str = Field(default="")

    @property
    def is_production(self) -> bool:
        return self.runtime_mode == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
