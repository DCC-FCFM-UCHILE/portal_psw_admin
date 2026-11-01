from core.functions import get_env_variable
from core.settings.base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = get_env_variable("DJANGO_ALLOWED_HOSTS").split(",")
CSRF_TRUSTED_ORIGINS = get_env_variable("DJANGO_CSRF_TRUSTED_ORIGINS").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_PATH = CSRF_COOKIE_PATH = get_env_variable("DJANGO_COOKIE_PATH", "/")

EMAIL_BACKEND = get_env_variable("DJANGO_EMAIL_BACKEND")
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_HOST = get_env_variable("DJANGO_EMAIL_HOST")
