# config/settings/staging.py
from .base import *

DEBUG = False

# Hard-allow your Render domain explicitly (plus localhost just in case)
ALLOWED_HOSTS = [
    "my-django-website-1.onrender.com",
    "localhost",
    "127.0.0.1",
    ".onrender.com",   # subdomains fallback
]

# CSRF must list the exact scheme+host (wildcards are flaky)
CSRF_TRUSTED_ORIGINS = [
    "https://my-django-website-1.onrender.com",
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
