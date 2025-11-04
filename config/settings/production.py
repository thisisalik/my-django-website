# config/settings/production.py
from .base import *
import os

DEBUG = False

# Add the exact Render hostname if present, plus your custom domains.
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = [
    "turtleapp.co",
    "www.turtleapp.co",
]
if RENDER_HOST:
    ALLOWED_HOSTS += [RENDER_HOST, ".onrender.com"]

CSRF_TRUSTED_ORIGINS = [
    "https://turtleapp.co",
    "https://www.turtleapp.co",
]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS += [f"https://{RENDER_HOST}"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Make static serving robust & cache-friendly in prod
STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}
