from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.text import capfirst
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


def nombre_suelto(permiso):
    tipo = permiso.content_type
    modelo = tipo.model_class()
    sujeto = capfirst(modelo._meta.verbose_name_plural) if modelo else f"{tipo.app_label}.{tipo.model}"
    clave = accion(permiso)
    return f"{sujeto}: {ACCIONES[clave].lower() if clave else permiso.name}"


class MatrizPermisos(forms.CheckboxSelectMultiple):
    template_name = "cuentas/widgets/permisos.html"

    def __init__(self, attrs=None, choices=()):
        super().__init__({"class": " ".join(CHECKBOX_CLASSES), **(attrs or {})}, choices)

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        opciones = {}
        for _, grupo, _ in contexto["widget"]["optgroups"]:
            for opcion in grupo:
                permiso = opcion["value"].instance
                clave = accion(permiso)
                opciones[(permiso.content_type.app_label, permiso.content_type.model, clave) if clave else permiso.pk] = opcion
                opcion["permiso"] = permiso

        secciones = []
        for titulo, filas in secciones_del_menu():
            tabla = []
            for nombre, modelo in filas:
                celdas = []
                for clave, verbo in ACCIONES.items():
                    opcion = opciones.pop((modelo._meta.app_label, modelo._meta.model_name, clave), None)
                    if opcion:
                        opcion["etiqueta"] = f"{verbo} {nombre.lower()}"
                    celdas.append(opcion)
                if any(celdas):
                    tabla.append({"nombre": nombre, "celdas": celdas})
            if tabla:
                secciones.append({"titulo": titulo, "filas": tabla})

        otros = sorted(opciones.values(), key=lambda opcion: nombre_suelto(opcion["permiso"]))
        for opcion in otros:
            opcion["etiqueta"] = nombre_suelto(opcion["permiso"])

        contexto["widget"].update(
            {
                "secciones": secciones,
                "acciones": ACCIONES.values(),
                "otros": otros,
                "otros_elegidos": sum(1 for opcion in otros if opcion["selected"]),
            }
        )
        return contexto


class CasillasDeGrupos(UnfoldAdminCheckboxSelectMultipleWidget):
    template_name = "cuentas/widgets/grupos.html"
