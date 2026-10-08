from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.text import capfirst

register = template.Library()


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
