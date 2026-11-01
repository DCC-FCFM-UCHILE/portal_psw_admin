import hashlib
import json
import logging
from functools import lru_cache
from urllib.parse import parse_qs, urlsplit

from django import template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.main import ORDER_VAR, PAGE_VAR
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from unfold.templatetags.unfold_list import unfold_vertical_filters

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
def formatos_archivo(accept):
    formatos = [formato.strip().lstrip(".").upper() for formato in str(accept).split(",") if formato.strip()]
    if len(formatos) < 2:
        return f"Formato {''.join(formatos)}"
    return f"Formatos {', '.join(formatos[:-1])} o {formatos[-1]}"


@register.filter
def describir_con(atributos, propia):
    otras = [descripcion for descripcion in str(atributos.get("aria-describedby", "")).split() if descripcion != propia]
    return {**atributos, "aria-describedby": " ".join([propia, *otras])}.items()


@register.filter
def grupos_visibles(navegacion):
    grupos = []
    for grupo in navegacion:
        items = [item for item in grupo.get("items", []) if item.get("has_permission")]
        if items:
            grupos.append({**grupo, "items": items})
    return grupos


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


@register.simple_tag
def rutas_listado():
    rutas = [reverse(f"admin:{m._meta.app_label}_{m._meta.model_name}_changelist") for m in admin.site._registry]
    return mark_safe(json.dumps(rutas))


@register.simple_tag
def url_pagina(cl, numero):
    return cl.get_query_string({PAGE_VAR: numero})


@register.simple_tag
def pagina_del_listado(cl):
    return cl.paginator.get_page(cl.page_num)


@register.simple_tag
def paginas_cercanas(cl, vecinas=1, extremos=1):
    total, actual, elipsis = cl.paginator.num_pages, cl.page_num, cl.paginator.ELLIPSIS
    if total <= 2 * (extremos + vecinas) + 3:
        return list(range(1, total + 1))
    desde = max(min(actual - vecinas, total - extremos - 2 * vecinas - 1), extremos + 2)
    hasta = min(max(actual + vecinas, extremos + 2 * vecinas + 2), total - extremos - 1)
    antes = [elipsis] if desde > extremos + 2 else [extremos + 1]
    despues = [elipsis] if hasta < total - extremos - 1 else [total - extremos]
    return [*range(1, extremos + 1), *antes, *range(desde, hasta + 1), *despues, *range(total - extremos + 1, total + 1)]


@register.simple_tag
def url_orden(cl, encabezado):
    orden = parse_qs(urlsplit(encabezado["url_primary"]).query).get(ORDER_VAR, [""])[0]
    return cl.get_query_string({ORDER_VAR: orden.split(".")[0]})


@register.simple_tag
def parametros_sin_filtro(cl):
    usados = {parametro for spec in unfold_vertical_filters(cl) for parametro in spec.used_parameters}
    return [(nombre, valor) for nombre, valores in cl.filter_params.items() if nombre not in usados for valor in valores]
