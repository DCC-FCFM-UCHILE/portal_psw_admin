import base64
import hashlib
from functools import lru_cache

from django.conf import settings
from django.template.loader import render_to_string

from interfaz.templatetags.interfaz import GUIONES_EN_LINEA, compactar
from postulaciones.correo import LOGO


def resumen(codigo):
    return f"'sha256-{base64.b64encode(hashlib.sha256(codigo.encode()).digest()).decode()}'"


def armar_politica():
    guiones = " ".join(resumen(compactar(render_to_string(plantilla))) for plantilla in GUIONES_EN_LINEA)
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src 'self' {guiones} 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            f"img-src 'self' data: {LOGO}",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
    )


politica_fija = lru_cache(maxsize=1)(armar_politica)


class PoliticaDeContenido:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        if respuesta.get("Content-Type", "").startswith("text/html"):
            politica = armar_politica() if settings.DEBUG else politica_fija()
            respuesta.headers.setdefault("Content-Security-Policy-Report-Only", politica)
        return respuesta
