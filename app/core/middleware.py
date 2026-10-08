import logging

from django.db import InterfaceError, OperationalError
from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class BaseNoDisponible:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (OperationalError, InterfaceError)):
            return None
        logger.error("Base de datos no disponible en %s", request.path, exc_info=exception)
        respuesta = HttpResponse(render_to_string("503.html"), status=503)
        respuesta["Retry-After"] = "120"
        return respuesta
