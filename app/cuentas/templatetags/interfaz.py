import hashlib
import logging
from functools import lru_cache

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils.text import capfirst

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def iniciales(usuario):
    nombre = f"{usuario.first_name[:1]}{usuario.last_name[:1]}"
    return (nombre or usuario.get_username()[:2]).upper()


@register.filter
def compactar(codigo):
    return "\n".join(linea.strip() for linea in str(codigo).splitlines() if linea.strip())


@register.filter
def nombre_archivo(archivo):
    return str(archivo.name).rsplit("/", 1)[-1] if archivo else ""


@register.filter
def sin_aplicacion(descripcion):
    return str(descripcion).split(" - ", 1)[-1]


@register.simple_tag(takes_context=True)
def migas(context):
    if context.get("migas_vista"):
        return context["migas_vista"]
    opciones = context.get("opts")
    titulo = str(context.get("title") or "")
    if not opciones:
        return {"ruta": [], "titulo": titulo or "Inicio"}
    listado = {"titulo": capfirst(opciones.verbose_name_plural), "enlace": ""}
    try:
        listado["enlace"] = reverse(f"admin:{opciones.app_label}_{opciones.model_name}_changelist")
    except NoReverseMatch:
        pass
    if context.get("cl"):
        return {"ruta": [], "titulo": listado["titulo"]}
    original = context.get("original")
    if original is not None and not isinstance(original, str) and context.get("change"):
        return {"ruta": [listado], "titulo": str(original)}
    return {"ruta": [listado], "titulo": titulo or str(original or "")}


def version_de_siluetas():
    contenido = render_to_string("components/siluetas/vistas.html")
    return hashlib.sha256(contenido.encode()).hexdigest()[:12]


version_fija = lru_cache(maxsize=1)(version_de_siluetas)


@register.simple_tag
def url_siluetas():
    try:
        version = version_de_siluetas() if settings.DEBUG else version_fija()
        return f"{reverse('siluetas')}?v={version}"
    except Exception:
        logger.exception("No se pudo armar la dirección de las siluetas")
        return ""
