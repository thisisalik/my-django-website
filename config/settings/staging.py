# config/settings/staging.py
from .base import *

DEBUG = False

# Staging can accept any host (Render assigns random subdomains)
ALLOWED_HOSTS = ["*"]

# Trust Render subdomains for CSRF (needed for forms, logins, etc.)
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]

# Basic security flags (same as you had)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
