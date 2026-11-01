import os

from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name, default=None):
    valor = os.environ.get(var_name, "")
    if not valor:
        if default is not None:
            return default
        raise ImproperlyConfigured(f"Falta la variable de entorno {var_name}")

    if valor.lower() == "true":
        return True
    if valor.lower() == "false":
        return False
    return valor
