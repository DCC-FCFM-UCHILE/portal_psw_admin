from django.contrib import admin
from django.utils.text import capfirst
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.ficha import SinGuardarYAgregarOtro
from core.listado import ListadoParcial
from postulaciones.models import ApprovedProject, Member


class MemberInline(TabularInline):
    model = Member
    fields = ["nombre", "es_visible"]
    extra = 0

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if campo is not None:
            campo.widget.attrs["aria-label"] = capfirst(db_field.verbose_name)
        return campo


@admin.register(ApprovedProject)
class ApprovedProjectAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, ModelAdmin):
    list_display = ["titulo", "convocatoria", "organizacion", "unidad", "postulante", "semestre", "anio", "tutor", "es_visible"]
    list_filter = ["es_visible"]
    search_fields = ["titulo", "postulacion__titulo"]
    list_select_related = ["postulacion__convocatoria", "postulacion__postulante", "postulacion__unidad__organizacion"]
    list_per_page = 10
    inlines = [MemberInline]

    @display(description="Convocatoria")
    def convocatoria(self, obj):
        return obj.postulacion.convocatoria if obj.postulacion else "-"

    @display(description="Organización")
    def organizacion(self, obj):
        return (obj.postulacion and obj.postulacion.organizacion) or "-"

    @display(description="Unidad")
    def unidad(self, obj):
        return (obj.postulacion and obj.postulacion.unidad) or "-"

    @display(description="Postulante")
    def postulante(self, obj):
        return obj.postulacion.postulante if obj.postulacion else "-"
