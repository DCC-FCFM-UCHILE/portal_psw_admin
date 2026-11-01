from django import forms
from django.contrib.admin.options import IS_POPUP_VAR
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
        contexto = respuesta.context_data if isinstance(respuesta, TemplateResponse) else None
        if contexto and "media" in contexto and not (IS_POPUP_VAR in request.GET or self.list_editable):
            media = contexto["media"]
            contexto["media"] = forms.Media(js=[ruta for ruta in media._js if not ruta.startswith("admin/js/")], css=media._css)
            contexto["sin_guiones_de_django"] = True
        if zona and contexto and "cl" in contexto:
            respuesta.template_name = FRAGMENTOS[zona]
        patch_vary_headers(respuesta, ["HX-Request", "HX-Target"])
        return respuesta
