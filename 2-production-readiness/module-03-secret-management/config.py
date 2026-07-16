import sys
from enum import Enum

from pydantic import Field, ValidationError
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    app_env: Environment = Field(
        ...,
        alias="APP_ENV"
    )

    cors_origin: str = Field(
        ...,
        alias="CORS_ORIGIN"
    )

    log_level: str = Field(
        "info",
        alias="LOG_LEVEL"
    )

    # Server
    port: int = Field(
        ...,
        ge=1,
        le=65535,
        alias="PORT"
    )

    # Database
    database_url: str = Field(
        ...,
        alias="DATABASE_URL"
    )

    # JWT
    jwt_secret: str = Field(
        ...,
        alias="JWT_SECRET"
    )

    jwt_algorithm: str = Field(
        "HS256",
        alias="JWT_ALGORITHM"
    )

    # Redis
    redis_url: str = Field(
        ...,
        alias="REDIS_URL"
    )

    # Analytics retention
    retention_days: int = Field(
        30,
        alias="RETENTION_DAYS"
    )


try:
    settings = Settings()

except ValidationError as e:
    print(
        "\n[Configuration Error] Environment validation failed!",
        file=sys.stderr
    )

    for error in e.errors():
        loc = " -> ".join(
            str(x)
            for x in error["loc"]
        )

        print(
            f"  - {loc}: {error['msg']}",
            file=sys.stderr
        )

    print(
        "\nPlease check your api/.env file.\n",
        file=sys.stderr
    )

    sys.exit(1)

except Exception as e:
    print(
        f"\n[Unexpected Configuration Error]: {e}\n",
        file=sys.stderr
    )

    sys.exit(1)