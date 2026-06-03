"""
Django settings for SwapCampus project.

环境切换：通过 DJANGO_ENV 环境变量控制
- DJANGO_ENV=dev   → 开发环境（默认）
- DJANGO_ENV=prod  → 生产环境
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

# ── 基础目录 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── 环境标识 ──────────────────────────────────────────────
ENV = config("DJANGO_ENV", default="dev")

# ── 密钥与调试 ────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="change-me-to-a-random-string")
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)

# ── 应用注册 ──────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "channels",
]

LOCAL_APPS = [
    "core",
    "apps.users",
    "apps.products",
    "apps.transactions",
    "apps.chat",
    "apps.admin_panel",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── 中间件 ────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # 尽早处理 CORS
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# ── 模板 ──────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── 数据库 ─────────────────────────────────────────────────
# 开发环境默认使用 SQLite（零配置，MySQL 仅生产/CI 使用）
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# MySQL 配置（生产环境时设置 DJANGO_ENV=prod，或在 .env 中设置 DB_ENGINE=mysql）
if config("DB_ENGINE", default="sqlite") == "mysql":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="swapcampus"),
        "USER": config("DB_USER", default="swapcampus"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }

# ── 测试环境：自动切换为 SQLite 内存数据库 ─────────────────
if "pytest" in sys.modules or "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

# ── 自定义用户模型 ────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

# ── 密码验证 ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── 国际化 ────────────────────────────────────────────────
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ── 静态文件 ──────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static/collected"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ── 媒体文件 ──────────────────────────────────────────────
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── 默认主键 ──────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ═══════════════════════════════════════════════════════════
# DRF 配置
# ═══════════════════════════════════════════════════════════
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.unified_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        # 开发环境开启可浏览 API
        *(["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
    ],
}

# ═══════════════════════════════════════════════════════════
# SimpleJWT 配置
# ═══════════════════════════════════════════════════════════
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_USER_CLASS": "apps.users.models.User",
}

# ═══════════════════════════════════════════════════════════
# DRF Spectacular（API 文档）
# ═══════════════════════════════════════════════════════════
SPECTACULAR_SETTINGS = {
    "TITLE": "SwapCampus API",
    "DESCRIPTION": "北京林业大学校园闲置物品交易平台",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ═══════════════════════════════════════════════════════════
# CORS
# ═══════════════════════════════════════════════════════════
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ═══════════════════════════════════════════════════════════
# Channels（Redis 作为 Channel Layer）
# ═══════════════════════════════════════════════════════════
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://127.0.0.1:6379/0")],
        },
    },
}

# ═══════════════════════════════════════════════════════════
# MinIO 对象存储
# ═══════════════════════════════════════════════════════════
MINIO_ENDPOINT = config("MINIO_ENDPOINT", default="127.0.0.1:9000")
MINIO_ACCESS_KEY = config("MINIO_ACCESS_KEY", default="minioadmin")
MINIO_SECRET_KEY = config("MINIO_SECRET_KEY", default="minioadmin")
MINIO_BUCKET = config("MINIO_BUCKET", default="swapcampus")
MINIO_SECURE = config("MINIO_SECURE", default=False, cast=bool)

# 媒体文件默认使用本地存储；配置 DEFAULT_FILE_STORAGE 可切换到 MinIO
if config("USE_MINIO_STORAGE", default=False, cast=bool):
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_ENDPOINT_URL = f"http{'s' if MINIO_SECURE else ''}://{MINIO_ENDPOINT}"
    AWS_ACCESS_KEY_ID = MINIO_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = MINIO_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME = MINIO_BUCKET
    AWS_S3_REGION_NAME = "us-east-1"
    AWS_S3_SIGNATURE_VERSION = "s3v4"

# ═══════════════════════════════════════════════════════════
# 生产环境覆盖
# ═══════════════════════════════════════════════════════════
if ENV == "prod":
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    # 关闭可浏览 API
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
    ]
