# config/settings/staging.py
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = ["*"]

# Get the actual Render hostname
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")  # Example: my-django-website-1.onrender.com

# Add both exact host and wildcard (safe)
CSRF_TRUSTED_ORIGINS = []
if render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")
CSRF_TRUSTED_ORIGINS.append("https://*.onrender.com")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
