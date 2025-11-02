from .base import *
import os

DEBUG = False

# Accept any host in staging (safe on Render) and honor proxy Host header
ALLOWED_HOSTS = ["*"]
USE_X_FORWARDED_HOST = True

# Trust the exact Render hostname + wildcard fallback
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or "my-django-website-1.onrender.com"
CSRF_TRUSTED_ORIGINS = [
    f"https://{render_host}",
    "https://*.onrender.com",
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
