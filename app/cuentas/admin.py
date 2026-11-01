from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from cuentas.widgets import CasillasDeGrupos, MatrizPermisos

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


@admin.register(User)
class UserAdmin(PermisosEnTabla, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "groups":
            campo.widget.can_add_related = False
        return campo


@admin.register(Group)
class GroupAdmin(PermisosEnTabla, BaseGroupAdmin, ModelAdmin):
    def has_module_permission(self, request):
        return False
