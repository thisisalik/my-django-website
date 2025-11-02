# config/settings/staging.py
from .base import *
import os

DEBUG = False

# Accept any host on staging
ALLOWED_HOSTS = ["*"]

# Trust your exact Render hostname (preferred) and the wildcard as fallback
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
CSRF_TRUSTED_ORIGINS = (
    [f"https://{RENDER_HOST}"] if RENDER_HOST else []
) + [
    "https://*.onrender.com",
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
