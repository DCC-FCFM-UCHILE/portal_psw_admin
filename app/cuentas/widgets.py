from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashWidget
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.urls import NoReverseMatch, reverse
from unfold.widgets import CHECKBOX_CLASSES, UnfoldAdminCheckboxSelectMultipleWidget

ACCIONES = {"view": "Ver", "add": "Agregar", "change": "Editar", "delete": "Eliminar"}


def secciones_del_menu():
    modelos = {}
    for modelo in admin.site._registry:
        try:
            modelos[reverse(f"admin:{modelo._meta.app_label}_{modelo._meta.model_name}_changelist")] = modelo
        except NoReverseMatch:
            continue
    for grupo in settings.UNFOLD["SIDEBAR"]["navigation"]:
        filas = [(str(item["title"]), modelos[str(item["link"])]) for item in grupo["items"] if str(item.get("link")) in modelos]
        if filas:
            yield str(grupo.get("title", "")), filas


def accion(permiso):
    prefijo, _, resto = permiso.codename.partition("_")
    return prefijo if prefijo in ACCIONES and resto == permiso.content_type.model else None


def opciones_por_permiso(grupos):
    opciones = {}
    for _, grupo, _ in grupos:
        for opcion in grupo:
            permiso = opcion["value"].instance
            clave = accion(permiso)
            opciones[(permiso.content_type.app_label, permiso.content_type.model, clave) if clave else permiso.pk] = opcion
            opcion["permiso"] = permiso
    return opciones


def fila_de_permisos(nombre, modelo, opciones):
    celdas = []
    for clave, verbo in ACCIONES.items():
        opcion = opciones.pop((modelo._meta.app_label, modelo._meta.model_name, clave), None)
        if opcion:
            opcion["etiqueta"] = f"{verbo} {nombre.lower()}"
        celdas.append({"verbo": verbo, "opcion": opcion})
    return {"nombre": nombre, "celdas": celdas} if any(celda["opcion"] for celda in celdas) else None


class MatrizPermisos(forms.CheckboxSelectMultiple):
    template_name = "cuentas/widgets/permisos.html"

    def __init__(self, attrs=None, choices=()):
        super().__init__({"class": " ".join(CHECKBOX_CLASSES), **(attrs or {})}, choices)

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        opciones = opciones_por_permiso(contexto["widget"]["optgroups"])
        secciones = []
        for titulo, filas in secciones_del_menu():
            tabla = [fila for fila in (fila_de_permisos(nombre, modelo, opciones) for nombre, modelo in filas) if fila]
            if tabla:
                secciones.append({"titulo": titulo, "filas": tabla})

        contexto["widget"].update(
            {
                "secciones": secciones,
                "acciones": ACCIONES.values(),
                "ajenos": [opcion for opcion in opciones.values() if opcion["selected"]],
            }
        )
        return contexto


class CasillasDeGrupos(UnfoldAdminCheckboxSelectMultipleWidget):
    template_name = "cuentas/widgets/grupos.html"


class AccesoAContrasena(ReadOnlyPasswordHashWidget):
    template_name = "cuentas/widgets/contrasena.html"

    def __init__(self, enlace, attrs=None):
        super().__init__(attrs)
        self.enlace = enlace

    def get_context(self, name, value, attrs):
        contexto = forms.Widget.get_context(self, name, value, attrs)
        contexto["widget"].update(
            {"enlace": self.enlace, "tiene_contrasena": bool(value) and not value.startswith(UNUSABLE_PASSWORD_PREFIX)}
        )
        return contexto
