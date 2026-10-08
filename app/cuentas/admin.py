from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.text import capfirst
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)

ACCIONES = {"add": "agregar", "change": "editar", "delete": "eliminar", "view": "ver"}


def nombre_app(etiqueta):
    try:
        return str(apps.get_app_config(etiqueta).verbose_name)
    except LookupError:
        return etiqueta


def nombre_permiso(permiso):
    tipo = permiso.content_type
    modelo = tipo.model_class()
    nombre_modelo = str(modelo._meta.verbose_name) if modelo else tipo.model
    accion = permiso.codename.split("_", 1)[0]
    texto = f"Puede {ACCIONES[accion]} {nombre_modelo}" if accion in ACCIONES else permiso.name
    return f"{capfirst(nombre_app(tipo.app_label))} | {capfirst(nombre_modelo)} | {texto}"


class PermisosEnEspanol:
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        campo = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name in ("permissions", "user_permissions"):
            campo.label_from_instance = nombre_permiso
        return campo


@admin.register(User)
class UserAdmin(PermisosEnEspanol, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(PermisosEnEspanol, BaseGroupAdmin, ModelAdmin):
    pass
