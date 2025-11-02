# config/settings/staging.py
from .base import *
import os

DEBUG = False

# Accept any host in staging (safe on Render)
ALLOWED_HOSTS = ["*"]

# Trust the exact Render hostname + a fallback wildcard
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or "my-django-website-1.onrender.com"
CSRF_TRUSTED_ORIGINS = [
    f"https://{render_host}",
    "https://*.onrender.com",
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
