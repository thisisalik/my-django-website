from .base import *
import os

DEBUG = False

RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = ["turtleapp.co", "www.turtleapp.co"]
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

# --- STATICFILES storage (change this line) ---
# Use compressed storage (no manifest) to avoid the ps.js mismatch.
STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
}

# Loosen manifest strictness just in case something references a missing file.
WHITENOISE_MANIFEST_STRICT = False
