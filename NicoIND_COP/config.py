"""
NicoIND — Nicolás Industrial Intelligence Dashboard
config.py — Configuración de la aplicación
Autor: Nicolás Rodríguez
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _fix_db_url(url: str) -> str:
    """Render entrega postgres://, SQLAlchemy necesita postgresql://"""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # ── Seguridad ───────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "nicond-super-secret-2024!")

    # ── Base de datos ───────────────────────────────────────
    _raw_db = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'nicond.db')}")
    SQLALCHEMY_DATABASE_URI     = _fix_db_url(_raw_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS   = {"pool_pre_ping": True}

    # ── Sesión ──────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = "Lax"

    # ── Archivos ────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024   # 32 MB
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, "static", "uploads")

    # ── App ─────────────────────────────────────────────────
    APP_NAME    = "NicoIND"
    APP_VERSION = "1.0.0"
    AUTHOR      = "Nicolás Rodríguez"
    COMPANY_DEF = "Demo Corp S.A."
