import re

from django.http import HttpResponsePermanentRedirect
from django.urls import get_script_prefix, path, re_path
from django.urls.resolvers import RoutePattern, URLResolver
from django.views.generic import RedirectView

MODELOS = {
    "applications/application/": "postulaciones/",
    "applications/organization/": "organizaciones/",
    "applications/unit/": "unidades/",
    "applications/candidate/": "postulantes/",
    "applications/approvedproject/": "proyectos/",
    "applications/member/": "integrantes/",
    "applications/announcement/": "convocatorias/",
    "commons/rulesapplications/": "convenios/",
    "auth/user/": "usuarios/",
    "auth/group/": "grupos/",
}

SITIO = {
    "login/": "ingresar/",
    "logout/": "salir/",
    "password_change/": "cambiar-contrasena/",
    "password_change/done/": "cambiar-contrasena/listo/",
}

FICHA = {
    "add/": "agregar/",
    "<path:object_id>/history/": "<path:object_id>/historial/",
    "<path:object_id>/delete/": "<path:object_id>/eliminar/",
    "<path:object_id>/change/": "<path:object_id>/",
    "<id>/password/": "<id>/contrasena/",
}

ANTIGUAS = [
    (r"^add/$", "agregar/"),
    (r"^(.+)/change/$", r"\1/"),
    (r"^(.+)/history/$", r"\1/historial/"),
    (r"^(.+)/delete/$", r"\1/eliminar/"),
    (r"^(\d+)/password/$", r"\1/contrasena/"),
]

RECUPERAR = {
    "password_reset/": "recuperar-contrasena/",
    "password_reset/done/": "recuperar-contrasena/enviado/",
}


def _ruta(patron):
    return str(patron.pattern) if isinstance(patron.pattern, RoutePattern) else None


def _copiar(patron, ruta):
    if isinstance(patron, URLResolver):
        return path(ruta, (patron.url_patterns, patron.app_name, patron.namespace))
    return path(ruta, patron.callback, patron.default_args, patron.name)


def _ficha(patrones):
    salida, vistos = [], set()
    for patron in patrones:
        ruta = _ruta(patron)
        if ruta == "<path:object_id>/" and patron.name is None:
            continue
        if (ruta, patron.name) in vistos:
            continue
        vistos.add((ruta, patron.name))
        salida.append(_copiar(patron, FICHA.get(ruta, ruta)))
    return salida


def traducir(patrones):
    salida = []
    for patron in patrones:
        ruta = _ruta(patron)
        if ruta in MODELOS:
            salida.append(path(MODELOS[ruta], (_ficha(patron.url_patterns), None, None)))
        elif ruta in SITIO:
            salida.append(_copiar(patron, SITIO[ruta]))
        elif patron.name == "app_list":
            salida.append(re_path(patron.pattern.regex.pattern, RedirectView.as_view(pattern_name="admin:index"), name="app_list"))
        else:
            salida.append(patron)
    return salida


def ruta_nueva(antigua):
    if antigua in SITIO:
        return SITIO[antigua]
    if antigua in RECUPERAR:
        return RECUPERAR[antigua]
    if antigua == "reset/done/":
        return "recuperar-contrasena/listo/"
    if antigua.startswith("reset/"):
        return "recuperar-contrasena/" + antigua.removeprefix("reset/")
    for prefijo, nuevo in MODELOS.items():
        if antigua.startswith(prefijo):
            resto = antigua[len(prefijo):]
            for patron, reemplazo in ANTIGUAS:
                if re.match(patron, resto):
                    return nuevo + re.sub(patron, reemplazo, resto)
            return nuevo + resto
    if re.fullmatch(r"(auth|commons|applications)/", antigua):
        return ""
    return antigua


def redirigir_antigua(request, antigua, prefijo=""):
    destino = get_script_prefix() + ruta_nueva(prefijo + antigua)
    if request.META.get("QUERY_STRING"):
        destino += "?" + request.META["QUERY_STRING"]
    return HttpResponsePermanentRedirect(destino)
