from core.functions import get_env_variable
from core.settings.base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = get_env_variable("DJANGO_ALLOWED_HOSTS").split(",")
CSRF_TRUSTED_ORIGINS = get_env_variable("DJANGO_CSRF_TRUSTED_ORIGINS").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
