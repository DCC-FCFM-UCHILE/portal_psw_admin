from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import sensitive_post_parameters_m
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, ExpressionWrapper, Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils.text import capfirst
from unfold.admin import ModelAdmin

from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.ficha import SinGuardarYAgregarOtro
from core.listado import ListadoParcial
from cuentas.forms import AltaUsuarioForm, CambioClaveForm, FichaUsuarioForm, IngresoForm
from cuentas.requisitos import pide_requisitos, responder
from cuentas.widgets import CasillasDeGrupos, MatrizPermisos

admin.site.login_form = IngresoForm
admin.site.unregister(User)
admin.site.unregister(Group)


def nombre_de_permiso(permiso):
    return f"{permiso.content_type.app_label}.{permiso.codename}"


def sin_dar_mas_de_lo_propio(formulario, usuario):
    if usuario.is_superuser:
        return formulario
    propios = usuario.get_all_permissions()

    class Formulario(formulario):
        def agregados(self, nombre):
            if nombre not in self.fields or self.fields[nombre].disabled or nombre not in self.cleaned_data:
                return []
            antes = set(getattr(self.instance, nombre).all()) if self.instance.pk else set()
            return [elemento for elemento in self.cleaned_data[nombre] if elemento not in antes]

        def clean(self):
            datos = super().clean()
            for nombre in ("permissions", "user_permissions"):
                ajenos = [permiso for permiso in self.agregados(nombre) if nombre_de_permiso(permiso) not in propios]
                if ajenos:
                    lista = ", ".join(f"«{permiso.name}»" for permiso in ajenos)
                    self.add_error(nombre, f"Solo puedes dar permisos que tu cuenta tiene. Quita {lista}.")
            grupos = [
                grupo
                for grupo in self.agregados("groups")
                if any(nombre_de_permiso(permiso) not in propios for permiso in grupo.permissions.select_related("content_type"))
            ]
            if grupos:
                lista = ", ".join(f"«{grupo.name}»" for grupo in grupos)
                self.add_error("groups", f"Solo puedes asignar grupos con permisos que tu cuenta tiene. Quita {lista}.")
            return datos

    return Formulario


class PermisosEnTabla:
    filter_horizontal = ()

    def get_form(self, request, obj=None, **kwargs):
        return sin_dar_mas_de_lo_propio(super().get_form(request, obj, **kwargs), request.user)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ("permissions", "user_permissions"):
            kwargs["widget"] = MatrizPermisos
            kwargs["queryset"] = db_field.remote_field.model.objects.select_related("content_type")
        elif db_field.name == "groups":
            kwargs["widget"] = CasillasDeGrupos
        return super().formfield_for_manytomany(db_field, request, **kwargs)


ACCESO_PROPIO = {
    "is_active": "No puedes desactivar tu propia cuenta.",
    "is_staff": "No puedes quitarte el acceso a la administración.",
    "is_superuser": "No puedes quitarte el superusuario.",
    "groups": "Tus grupos los cambia otra persona que administre las cuentas.",
    "user_permissions": "Tus permisos los cambia otra persona que administre las cuentas.",
}


def es_superusuario_ajeno(request, obj):
    return obj is not None and obj.is_superuser and not request.user.is_superuser


def sin_relaciones_internas(modelo, borrados, cantidades):
    intermedias = [campo.remote_field.through._meta for campo in modelo._meta.many_to_many if campo.remote_field.through._meta.auto_created]
    nombres = tuple(f"{capfirst(opciones.verbose_name)}: " for opciones in intermedias)
    plurales = {str(opciones.verbose_name_plural) for opciones in intermedias}

    def limpiar(lista):
        limpia = []
        for elemento in lista:
            if isinstance(elemento, list):
                hijos = limpiar(elemento)
                if hijos:
                    limpia.append(hijos)
            elif not str(elemento).startswith(nombres):
                limpia.append(elemento)
        return limpia

    return limpiar(borrados), {nombre: cantidad for nombre, cantidad in cantidades.items() if str(nombre) not in plurales}


@admin.register(User)
class UserAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, PermisosEnTabla, BaseUserAdmin, ModelAdmin):
    form = FichaUsuarioForm
    add_form = AltaUsuarioForm
    change_password_form = CambioClaveForm
    readonly_fields = ("last_login", "date_joined")
    list_per_page = 10

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "groups":
            campo.widget.can_add_related = False
        return campo

    def get_form(self, request, obj=None, **kwargs):
        formulario = super().get_form(request, obj, **kwargs)
        if obj is not None and obj.pk == request.user.pk:
            for nombre, ayuda in ACCESO_PROPIO.items():
                if nombre in formulario.base_fields:
                    formulario.base_fields[nombre].disabled = True
                    formulario.base_fields[nombre].help_text = ayuda
        elif not request.user.is_superuser and "is_superuser" in formulario.base_fields:
            formulario.base_fields["is_superuser"].disabled = True
            formulario.base_fields["is_superuser"].help_text = "Solo lo cambia un superusuario."
        formulario.cambia_contrasena = not es_superusuario_ajeno(request, obj)
        return formulario

    def get_fieldsets(self, request, obj=None):
        grupos = super().get_fieldsets(request, obj)
        if es_superusuario_ajeno(request, obj):
            (nombre, opciones), *resto = grupos
            return [(nombre, {**opciones, "description": "Las cuentas de superusuario solo las cambia otro superusuario."}), *resto]
        if obj is None or obj.pk != request.user.pk:
            return grupos
        return [
            (nombre, {**opciones, "description": "Tu propio acceso lo cambia otra persona que administre las cuentas."})
            if "is_active" in opciones.get("fields", ())
            else (nombre, opciones)
            for nombre, opciones in grupos
        ]

    def get_queryset(self, request):
        solo_lectura = Q(pk__in=[]) if request.user.is_superuser else Q(is_superuser=True)
        return (
            super()
            .get_queryset(request)
            .annotate(
                es_propia=ExpressionWrapper(Q(pk=request.user.pk), output_field=BooleanField()),
                solo_lectura=ExpressionWrapper(solo_lectura, output_field=BooleanField()),
            )
        )

    @sensitive_post_parameters_m
    def add_view(self, request, form_url="", extra_context=None):
        if pide_requisitos(request):
            if not self.has_add_permission(request):
                raise PermissionDenied
            return responder(self.get_form(request)(request.POST))
        return super().add_view(request, form_url, extra_context)

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=""):
        if pide_requisitos(request):
            usuario = self.get_object(request, unquote(id))
            if usuario is None:
                raise Http404
            if not self.has_change_permission(request, usuario):
                raise PermissionDenied
            return responder(self.change_password_form(usuario, request.POST))
        return super().user_change_password(request, id, form_url)

    def has_change_permission(self, request, obj=None):
        if es_superusuario_ajeno(request, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.pk == request.user.pk or es_superusuario_ajeno(request, obj):
            return False
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        if str(object_id) == str(request.user.pk):
            messages.warning(
                request, "Tu propia cuenta no se puede eliminar desde aquí. Pídeselo a otra persona que administre las cuentas."
            )
            return redirect("admin:auth_user_change", object_id)
        if not request.user.is_superuser and User.objects.filter(pk=object_id, is_superuser=True).exists():
            messages.warning(request, "Las cuentas de superusuario solo las elimina otro superusuario.")
            return redirect("admin:auth_user_change", object_id)
        return super().delete_view(request, object_id, extra_context)

    def get_deleted_objects(self, objs, request):
        borrados, cantidades, faltantes, protegidos = super().get_deleted_objects(objs, request)
        borrados, cantidades = sin_relaciones_internas(self.model, borrados, cantidades)
        motivos = set()
        if any(obj.pk == request.user.pk for obj in objs):
            motivos.add("tu propia cuenta (quítala de la selección)")
        if any(es_superusuario_ajeno(request, obj) for obj in objs):
            motivos.add("las cuentas de superusuario (quítalas de la selección)")
        return borrados, cantidades, motivos or faltantes, protegidos


@admin.register(Group)
class GroupAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, PermisosEnTabla, BaseGroupAdmin, ModelAdmin):
    def has_module_permission(self, request):
        return False
