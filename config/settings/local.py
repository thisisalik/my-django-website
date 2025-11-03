from .base import *

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1", "http://localhost"]

# Optional: keep emails in console locally
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
