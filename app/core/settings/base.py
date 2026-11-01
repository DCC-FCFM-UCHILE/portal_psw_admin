from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy

from core.functions import get_env_variable

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = get_env_variable("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
    "interfaz",
    "cuentas",
    "convenios",
    "postulaciones",
]

MIGRATION_MODULES = {
    "commons": None,
    "applications": None,
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "interfaz.politica.PoliticaDeContenido",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.BaseNoDisponible",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "_templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


DATABASES = {
    "default": {
        "ENGINE": get_env_variable("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": get_env_variable("DJANGO_DB_NAME", "portal_psw"),
        "USER": get_env_variable("DJANGO_DB_USER", ""),
        "PASSWORD": get_env_variable("DJANGO_DB_PASSWORD", ""),
        "HOST": get_env_variable("DJANGO_DB_HOST", ""),
        "PORT": get_env_variable("DJANGO_DB_PORT", ""),
        "TEST": {"NAME": "test_portal_psw_admin"},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = reverse_lazy("admin:login")
LOGIN_REDIRECT_URL = reverse_lazy("admin:index")

SESSION_COOKIE_AGE = 8 * 60 * 60


LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "_locale"]

FORM_RENDERER = "interfaz.formularios.Renderizador"


STATIC_URL = "static/"
STATIC_ROOT = get_env_variable("DJANGO_STATIC_ROOT", "/static")
STATICFILES_DIRS = [BASE_DIR / "_staticfiles"]

MEDIA_URL = "media/"
MEDIA_ROOT = get_env_variable("DJANGO_MEDIA_ROOT", "/media")


EMAIL_BACKEND = get_env_variable("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = get_env_variable("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(get_env_variable("DJANGO_EMAIL_PORT", 587))
EMAIL_USE_TLS = get_env_variable("DJANGO_EMAIL_USE_TLS", True) in (True, "1")
EMAIL_HOST_USER = get_env_variable("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env_variable("DJANGO_EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = get_env_variable("DJANGO_DEFAULT_FROM_EMAIL", "no-reply@dcc.uchile.cl")
EMAIL_TIMEOUT = 10

URL_PORTAL_PUBLICO = get_env_variable("DJANGO_URL_PORTAL_PUBLICO", "")


def puede(permiso):
    return lambda request: request.user.has_perm(permiso)


def entrada(titulo, icono, modelo):
    app, nombre = modelo.split(".")
    return {
        "title": titulo,
        "icon": icono,
        "link": reverse_lazy(f"admin:{app}_{nombre}_changelist"),
        "permission": puede(f"{app}.view_{nombre}"),
    }


NAVEGACION = [
    {
        "items": [
            {"title": "Inicio", "icon": "home", "link": reverse_lazy("admin:index")},
        ],
    },
    {
        "title": "Postulaciones",
        "items": [
            entrada("Postulaciones", "assignment", "applications.application"),
            entrada("Organizaciones", "domain", "applications.organization"),
            entrada("Unidades", "account_tree", "applications.unit"),
            entrada("Postulantes", "badge", "applications.candidate"),
        ],
    },
    {
        "title": "Proyectos",
        "items": [
            entrada("Proyectos", "rocket_launch", "applications.approvedproject"),
            entrada("Integrantes", "group", "applications.member"),
        ],
    },
    {
        "title": "Convocatorias",
        "items": [
            entrada("Convenios", "description", "commons.rulesapplications"),
            entrada("Convocatorias", "event", "applications.announcement"),
            entrada("Usuarios", "person", "auth.user"),
        ],
    },
]

GUIONES = [
    "tema",
    "menus",
    "seleccion",
    "formularios",
    "capas",
    "emergentes",
    "tablas",
    "listado",
    "buscador",
    "cajon",
    "sesion",
    "requisitos",
]

UNFOLD = {
    "SITE_TITLE": "Portal PSW · Administración",
    "SITE_HEADER": "Portal PSW",
    "SITE_SUBHEADER": "Administración",
    "SITE_URL": URL_PORTAL_PUBLICO or None,
    "SITE_SYMBOL": "school",
    "SITE_FAVICONS": [
        {"rel": "icon", "sizes": "any", "type": "image/x-icon", "href": lambda request: static("images/favicon/favicon.ico")},
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "BORDER_RADIUS": "8px",
    "DASHBOARD_CALLBACK": "postulaciones.inicio.indicadores",
    "SCRIPTS": [lambda request, nombre=nombre: static(f"js/administrativo/{nombre}.js") for nombre in GUIONES],
    "COLORS": {
        "base": {
            "50": "#f4f6fa",
            "100": "#edeff3",
            "200": "#e3e7ef",
            "300": "#cdd2db",
            "400": "#9aa1ac",
            "500": "#646e7a",
            "600": "#4b5563",
            "700": "#374151",
            "800": "#2b2f36",
            "900": "#1d2025",
            "950": "#15171b",
        },
        "primary": {
            "50": "#fef2f2",
            "100": "#fee2e2",
            "200": "#fecaca",
            "300": "#fca5a5",
            "400": "#f87171",
            "500": "#ef6b6b",
            "600": "#b71c1c",
            "700": "#8b1515",
            "800": "#761212",
            "900": "#5f0f0f",
            "950": "#3b0808",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "#333333",
            "important-dark": "var(--color-base-100)",
        },
    },
    "COMMAND": {
        "search_models": True,
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": NAVEGACION,
    },
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "estandar": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "estandar"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
