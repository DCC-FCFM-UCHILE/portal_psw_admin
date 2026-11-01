from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import BooleanField, ExpressionWrapper, Q
from django.shortcuts import redirect
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserCreationForm

from core.acciones import AccionesDeFila
from core.listado import ListadoParcial
from cuentas.forms import FichaUsuarioForm, IngresoForm
from cuentas.widgets import CasillasDeGrupos, MatrizPermisos

admin.site.login_form = IngresoForm
admin.site.unregister(User)
admin.site.unregister(Group)


class PermisosEnTabla:
    filter_horizontal = ()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ("permissions", "user_permissions"):
            kwargs["widget"] = MatrizPermisos
            kwargs["queryset"] = db_field.remote_field.model.objects.select_related("content_type")
        elif db_field.name == "groups":
            kwargs["widget"] = CasillasDeGrupos
        return super().formfield_for_manytomany(db_field, request, **kwargs)


ACCESO_PROPIO = ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]


@admin.register(User)
class UserAdmin(ListadoParcial, AccionesDeFila, PermisosEnTabla, BaseUserAdmin, ModelAdmin):
    form = FichaUsuarioForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_per_page = 10

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "groups":
            campo.widget.can_add_related = False
        return campo

    def get_form(self, request, obj=None, **kwargs):
        formulario = super().get_form(request, obj, **kwargs)
        if obj is not None and obj.pk == request.user.pk:
            for nombre in ACCESO_PROPIO:
                if nombre in formulario.base_fields:
                    formulario.base_fields[nombre].disabled = True
                    formulario.base_fields[nombre].help_text = ""
        return formulario

    def get_fieldsets(self, request, obj=None):
        grupos = super().get_fieldsets(request, obj)
        if obj is None or obj.pk != request.user.pk:
            return grupos
        return [
            (nombre, {**opciones, "description": "Tu propio acceso lo cambia otra persona que administre las cuentas."})
            if "is_active" in opciones.get("fields", ())
            else (nombre, opciones)
            for nombre, opciones in grupos
        ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(es_propia=ExpressionWrapper(Q(pk=request.user.pk), output_field=BooleanField()))

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.pk == request.user.pk:
            return False
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        if str(object_id) == str(request.user.pk):
            messages.warning(request, "Tu propia cuenta no se puede eliminar desde aquí. Pídeselo a otra persona que administre las cuentas.")
            return redirect("admin:auth_user_change", object_id)
        return super().delete_view(request, object_id, extra_context)

    def get_deleted_objects(self, objs, request):
        borrados, cantidades, faltantes, protegidos = super().get_deleted_objects(objs, request)
        if any(obj.pk == request.user.pk for obj in objs):
            faltantes = {"tu propia cuenta (quítala de la selección)"}
        return borrados, cantidades, faltantes, protegidos


@admin.register(Group)
class GroupAdmin(ListadoParcial, AccionesDeFila, PermisosEnTabla, BaseGroupAdmin, ModelAdmin):
    def has_module_permission(self, request):
        return False
