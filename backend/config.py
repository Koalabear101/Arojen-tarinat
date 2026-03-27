"""Application configuration for different environments."""
from __future__ import annotations

import os


class Config:
    """Base configuration."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG: bool = False
    TESTING: bool = False
    BOARD_WIDTH: int = 10
    BOARD_HEIGHT: int = 10
    MAX_TURNS: int = 30
    LOG_LEVEL: str = "INFO"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    LOG_LEVEL = "WARNING"


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    LOG_LEVEL = "DEBUG"


CONFIG_MAP: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(env: str | None = None) -> Config:
    """Return configuration for the given environment name."""
    env = env or os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, DevelopmentConfig)()
