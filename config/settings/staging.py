from .base import *
DEBUG = False
ALLOWED_HOSTS = ["*"]  # safe for onrender.com with DEBUG=False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
