# config/settings/production.py
from .base import *

DEBUG = False

ALLOWED_HOSTS = ["turtleapp.co", "www.turtleapp.co"]
CSRF_TRUSTED_ORIGINS = ["https://turtleapp.co", "https://www.turtleapp.co"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True