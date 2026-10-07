from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RelatedDropdownFilter
from unfold.decorators import action, display

from postulaciones.models import Announcement, Application, ApprovedProject, Candidate, Member, Organization, Unit
from postulaciones.views import CorreoPostulanteView

ESTADOS = {
    Application.Estado.CREADA: "info",
    Application.Estado.ACEPTADA: "success",
    Application.Estado.RECHAZADA: "danger",
}


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    list_display = ["__str__", "inicio", "cierre", "convenio", "ver_postulaciones"]
    search_fields = ["anio"]
    list_per_page = 10

    @display(description="Postulaciones")
    def ver_postulaciones(self, obj):
        url = reverse("admin:applications_application_changelist")
        return format_html('<a href="{}?convocatoria__id__exact={}" class="text-primary-600">Ver postulaciones</a>', url, obj.pk)


@admin.register(Application)
class ApplicationAdmin(ModelAdmin):
    list_display = ["titulo", "convocatoria", "organizacion", "unidad", "postulante", "mostrar_estado", "fue_notificada", "perfil"]
    list_display_links = ["titulo"]
    list_filter = ["estado", ("convocatoria", RelatedDropdownFilter)]
    list_filter_submit = True
    search_fields = ["titulo", "unidad__nombre", "unidad__organizacion__nombre"]
    list_select_related = ["convocatoria", "postulante", "unidad__organizacion"]
    list_per_page = 10
    actions = ["aceptar", "rechazar"]
    actions_row = ["notificar", "contactar"]
    actions_detail = ["notificar", "contactar"]

    def get_actions(self, request):
        acciones = super().get_actions(request)
        acciones.pop("delete_selected", None)
        return acciones

    def get_urls(self):
        vistas = [
            path(
                f"<int:pk>/{tipo}/correo/",
                self.admin_site.admin_view(CorreoPostulanteView.as_view(model_admin=self, tipo=tipo)),
                name=f"applications_application_{tipo}_correo",
            )
            for tipo in ("notificar", "contactar")
        ]
        return vistas + super().get_urls()

    @display(description="Organización")
    def organizacion(self, obj):
        return obj.organizacion or "Sin organización"

    @display(description="Estado", label=ESTADOS)
    def mostrar_estado(self, obj):
        return obj.estado, obj.get_estado_display()

    @display(description="Perfil de proyecto")
    def perfil(self, obj):
        if not obj.archivo:
            return "Sin archivo"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" class="text-primary-600">Descargar<span class="sr-only">'
            " el perfil de {} (se abre en otra pestaña)</span></a>",
            obj.archivo.url,
            obj.titulo,
        )

    @action(description="Aceptar", permissions=["change"])
    def aceptar(self, request, queryset):
        queryset.update(estado=Application.Estado.ACEPTADA, fue_notificada=False)
        messages.success(request, "Postulaciones actualizadas a aceptadas.")

    @action(description="Rechazar", permissions=["change"])
    def rechazar(self, request, queryset):
        queryset.update(estado=Application.Estado.RECHAZADA, fue_notificada=False)
        messages.success(request, "Postulaciones actualizadas a rechazadas.")

    @action(description="Notificar", url_path="notificar", permissions=["change"], icon="mail")
    def notificar(self, request, object_id):
        return redirect("admin:applications_application_notificar_correo", pk=object_id)

    @action(description="Contactar", url_path="contactar", permissions=["change"], icon="person")
    def contactar(self, request, object_id):
        return redirect("admin:applications_application_contactar_correo", pk=object_id)


class MemberInline(TabularInline):
    model = Member
    fields = ["nombre", "es_visible"]
    extra = 0


@admin.register(ApprovedProject)
class ApprovedProjectAdmin(ModelAdmin):
    list_display = ["titulo", "convocatoria", "organizacion", "unidad", "postulante", "semestre", "anio", "tutor", "es_visible"]
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


@admin.register(Candidate)
class CandidateAdmin(ModelAdmin):
    list_display = ["nombre", "correo", "organizacion"]
    search_fields = ["organizacion__nombre", "nombre", "correo"]
    list_select_related = ["organizacion"]
    list_per_page = 10


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ["rut", "nombre", "rubro"]
    search_fields = ["rut", "nombre", "rubro"]
    list_per_page = 10


@admin.register(Unit)
class UnitAdmin(ModelAdmin):
    list_display = ["id", "nombre", "organizacion", "esta_vetada"]
    search_fields = ["nombre", "organizacion__nombre", "organizacion__rut"]
    list_select_related = ["organizacion"]
    list_per_page = 10


@admin.register(Member)
class MemberAdmin(ModelAdmin):
    list_display = ["nombre", "proyecto", "es_visible"]
    search_fields = ["proyecto__titulo", "nombre"]
    list_select_related = ["proyecto"]
    list_per_page = 10
