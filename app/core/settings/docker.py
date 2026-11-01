from core.functions import get_env_variable
from core.settings.base import *  # noqa: F401,F403

DEBUG = True

_hosts_locales = [h for h in get_env_variable("DJANGO_HOSTS_LOCALES", "").split(",") if h]

ALLOWED_HOSTS = ["localhost", "127.0.0.1", *_hosts_locales]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8003",
    "http://127.0.0.1:8003",
    *(f"http://{h}:8003" for h in _hosts_locales),
]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "core.estaticos.ConVersion"},
}
