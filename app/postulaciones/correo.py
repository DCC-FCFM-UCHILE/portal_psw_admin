import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def enviar(correo, asunto, contenido):
    html = render_to_string("postulaciones/correo/notificacion.html", {"asunto": asunto, "contenido": contenido})
    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=strip_tags(contenido),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[correo],
    )
    mensaje.attach_alternative(html, "text/html")
    try:
        return mensaje.send() == 1
    except Exception:
        logger.exception("No se pudo enviar el correo a %s", correo)
        return False
