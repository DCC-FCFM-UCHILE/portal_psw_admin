from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session


def renovar(sesion):
    sesion.set_expiry(timedelta(seconds=settings.SESSION_COOKIE_AGE))


def vencimiento(sesion):
    if sesion.get("_session_expiry"):
        return sesion.get_expiry_date()
    guardada = Session.objects.filter(session_key=sesion.session_key).values_list("expire_date", flat=True).first()
    return guardada or sesion.get_expiry_date()


def en_milisegundos(sesion):
    return int(vencimiento(sesion).timestamp() * 1000)
