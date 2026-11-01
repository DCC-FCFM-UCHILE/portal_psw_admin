from django import forms
from django.template.response import TemplateResponse
from django.utils.cache import patch_vary_headers

SIN_USO = {
    "admin/js/actions.js",
    "admin/js/urlify.js",
    "admin/js/prepopulate.js",
    "admin/js/vendor/xregexp/xregexp.js",
    "admin/js/vendor/xregexp/xregexp.min.js",
}

FRAGMENTOS = {
    "listado": "admin/listado_parcial.html",
    "resultados-listado": "admin/listado_resultados.html",
}


def zona_pedida(request):
    if request.headers.get("HX-Request") != "true":
        return None
    zona = request.headers.get("HX-Target")
    return zona if zona in FRAGMENTOS else None


class ListadoParcial:
    acciones_en_listado = ()

    @property
    def media(self):
        media = super().media
        return forms.Media(js=[ruta for ruta in media._js if ruta not in SIN_USO], css=media._css)

    def changelist_view(self, request, extra_context=None):
        respuesta = super().changelist_view(request, extra_context)
        zona = zona_pedida(request)
        if zona and isinstance(respuesta, TemplateResponse) and "cl" in (respuesta.context_data or {}):
            respuesta.template_name = FRAGMENTOS[zona]
        patch_vary_headers(respuesta, ["HX-Request", "HX-Target"])
        return respuesta
