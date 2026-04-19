"""Configuration de l'application Flask Hevy-Web.

Plusieurs classes de config permettent de basculer entre environnements
(dev, test, prod) via la variable d'environnement FLASK_ENV.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    """Configuration partagée entre tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Préférences utilisateur par défaut
    DEFAULT_UNIT_SYSTEM = os.environ.get("DEFAULT_UNIT_SYSTEM", "metric")

    # Compte admin initial (seedé au premier lancement)
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30  # 30 jours


class DevConfig(BaseConfig):
    """Configuration de développement."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'hevy.db'}"
    )


class TestConfig(BaseConfig):
    """Configuration pour les tests (base SQLite en mémoire)."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"


class ProdConfig(BaseConfig):
    """Configuration de production."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'hevy.db'}"
    )
    SESSION_COOKIE_SECURE = True


def get_config(name: str | None = None):
    """Retourne la classe de config correspondant au nom ou à FLASK_ENV."""
    env = (name or os.environ.get("FLASK_ENV", "development")).lower()
    return {
        "development": DevConfig,
        "dev": DevConfig,
        "testing": TestConfig,
        "test": TestConfig,
        "production": ProdConfig,
        "prod": ProdConfig,
    }.get(env, DevConfig)
