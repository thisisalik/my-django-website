# config/settings/staging.py
from .base import *
import os

DEBUG = False

# Exact Render hostname from env; fall back to your service name if present
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME") or "my-django-website-1.onrender.com"

# Be explicit; avoid "*" so DisallowedHost can't trigger via odd X-Forwarded-Host
ALLOWED_HOSTS = [
    render_host,
    ".onrender.com",
]

# CSRF must be exact origins (no wildcard). Add only the concrete Render origin.
CSRF_TRUSTED_ORIGINS = [
    f"https://{render_host}",
]

# Trust proxy proto for HTTPS is already set in base (SECURE_PROXY_SSL_HEADER)
# Do NOT set USE_X_FORWARDED_HOST here.

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
<<<<<<< HEAD
CSRF_COOKIE_SECURE = True
<<<<<<< HEAD
=======
CSRF_COOKIE_SECURE = True
>>>>>>> staging
=======
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True
>>>>>>> staging
