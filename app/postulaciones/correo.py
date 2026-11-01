import logging
import re
from html import unescape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

LOGO = "https://dcc.uchile.cl/static/images/H-lg.png"


def texto_plano(contenido):
    texto = re.sub(r"<br\s*/?>", "\n", contenido, flags=re.IGNORECASE)
    texto = re.sub(r"</(p|div|h[1-6]|li|blockquote|pre)>", "\n\n", texto, flags=re.IGNORECASE)
    texto = unescape(strip_tags(texto)).replace("\xa0", " ")
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def enviar(correo, asunto, contenido):
    html = render_to_string("postulaciones/correo/notificacion.html", {"asunto": asunto, "contenido": contenido, "logo": LOGO})
    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano(contenido),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[correo],
    )
    mensaje.attach_alternative(html, "text/html")
    try:
        return mensaje.send() == 1
    except Exception:
        logger.exception("No se pudo enviar el correo a %s", correo)
        return False
