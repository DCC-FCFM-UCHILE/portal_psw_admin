from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import capfirst
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RelatedDropdownFilter
from unfold.contrib.filters.forms import DropdownForm
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminSelectWidget

from core.acciones import AccionesDeFila
from postulaciones import historial
from postulaciones.models import Announcement, Application, ApprovedProject, Candidate, Member, Organization, Unit
from postulaciones.views import CorreoPostulanteView

ESTADOS = {
    Application.Estado.CREADA: "warning",
    Application.Estado.ACEPTADA: "success",
    Application.Estado.RECHAZADA: "danger",
}


class FormularioDesplegable(DropdownForm):
    widget = UnfoldAdminSelectWidget()

    class Media:
        extend = False


class ConvocatoriaFilter(RelatedDropdownFilter):
    form_class = FormularioDesplegable


class FormatosDeArchivo:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, models.FileField) and campo is not None:
            validadores = [validador for validador in db_field.validators if isinstance(validador, FileExtensionValidator)]
            extensiones = [f".{extension}" for validador in validadores for extension in validador.allowed_extensions or []]
            if extensiones:
                campo.widget.attrs["accept"] = ",".join(extensiones)
        return campo


class NotificacionFilter(admin.SimpleListFilter):
    title = "notificación"
    parameter_name = "notificacion"

    def lookups(self, request, model_admin):
        return [("pendiente", "Resuelta sin notificar"), ("notificada", "Notificada")]

    def queryset(self, request, queryset):
        if self.value() == "pendiente":
            return queryset.exclude(estado=Application.Estado.CREADA).filter(fue_notificada=False)
        if self.value() == "notificada":
            return queryset.filter(fue_notificada=True)
        return queryset


@admin.register(Announcement)
class AnnouncementAdmin(AccionesDeFila, ModelAdmin):
    list_display = ["__str__", "inicio", "cierre", "convenio", "ver_postulaciones"]
    search_fields = ["anio"]
    list_per_page = 10

    @display(description="Postulaciones")
    def ver_postulaciones(self, obj):
        url = reverse("admin:applications_application_changelist")
        return format_html('<a href="{}?convocatoria__id__exact={}" class="enlace">Ver postulaciones</a>', url, obj.pk)


@admin.register(Application)
class ApplicationAdmin(AccionesDeFila, FormatosDeArchivo, ModelAdmin):
    list_display = ["titulo", "convocatoria", "organizacion", "unidad", "postulante", "mostrar_estado", "fue_notificada", "perfil"]
    list_display_links = ["titulo"]
    list_filter = ["estado", NotificacionFilter, ("convocatoria", ConvocatoriaFilter)]
    list_filter_submit = True
    search_fields = ["titulo", "unidad__nombre", "unidad__organizacion__nombre"]
    list_select_related = ["convocatoria", "postulante", "unidad__organizacion"]
    list_per_page = 10
    actions = ["aceptar", "rechazar"]
    actions_row = ["editar_fila", "notificar", "contactar", "eliminar_fila"]
    actions_detail = ["notificar", "contactar"]
    list_before_template = "postulaciones/admin/filtros_estado.html"
    change_form_before_template = "postulaciones/admin/resumen_postulacion.html"

    def changelist_view(self, request, extra_context=None):
        respuesta = super().changelist_view(request, extra_context)
        if hasattr(respuesta, "context_data") and "cl" in respuesta.context_data:
            respuesta.context_data["filtros_estado"] = self.filtros_estado(request)
        return respuesta

    def filtros_estado(self, request):
        postulaciones = self.get_queryset(request)
        convocatoria = request.GET.get("convocatoria__id__exact")
        if convocatoria and convocatoria.isdigit():
            postulaciones = postulaciones.filter(convocatoria_id=convocatoria)
        busqueda = request.GET.get("q")
        if busqueda:
            postulaciones, _ = self.get_search_results(request, postulaciones, busqueda)
        cantidades = dict(postulaciones.order_by().values_list("estado").annotate(total=Count("id")))
        actual = request.GET.get("estado__exact", "")
        parametros = request.GET.copy()
        parametros.pop("p", None)
        parametros.pop("estado__exact", None)
        filtros = [{"nombre": "Todas", "valor": "", "total": sum(cantidades.values())}]
        filtros += [{"nombre": nombre, "valor": valor, "total": cantidades.get(valor, 0)} for valor, nombre in Application.Estado.choices]
        for filtro in filtros:
            consulta = parametros.copy()
            if filtro["valor"]:
                consulta["estado__exact"] = filtro["valor"]
            filtro["enlace"] = f"?{consulta.urlencode()}" if consulta else "?"
            filtro["actual"] = filtro["valor"] == actual
        return filtros

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if object_id and str(object_id).isdigit():
            registros = (
                LogEntry.objects.filter(content_type=ContentType.objects.get_for_model(Application), object_id=str(object_id))
                .select_related("user")
                .order_by("-action_time")[:4]
            )
            extra_context["historial"] = [
                {
                    "quien": registro.user.get_full_name() or registro.user.get_username(),
                    "verbo": historial.verbos(registro)[1],
                    "cuando": registro.action_time,
                }
                for registro in registros
            ]
        return super().change_view(request, object_id, form_url, extra_context)

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
            '<a href="{}" target="_blank" rel="noopener" class="enlace">Descargar<span class="sr-only">'
            " el perfil de {} (se abre en otra pestaña)</span></a>",
            obj.archivo.url,
            obj.titulo,
        )

    @action(description="Aceptar", permissions=["change"])
    def aceptar(self, request, queryset):
        postulaciones = list(queryset)
        queryset.update(estado=Application.Estado.ACEPTADA, fue_notificada=False)
        historial.registrar(request, postulaciones, historial.ACEPTADA)
        messages.success(request, "Postulaciones actualizadas a aceptadas.")

    @action(description="Rechazar", permissions=["change"])
    def rechazar(self, request, queryset):
        postulaciones = list(queryset)
        queryset.update(estado=Application.Estado.RECHAZADA, fue_notificada=False)
        historial.registrar(request, postulaciones, historial.RECHAZADA)
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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if campo is not None:
            campo.widget.attrs["aria-label"] = capfirst(db_field.verbose_name)
        return campo


@admin.register(ApprovedProject)
class ApprovedProjectAdmin(AccionesDeFila, ModelAdmin):
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


@admin.register(Candidate)
class CandidateAdmin(AccionesDeFila, ModelAdmin):
    list_display = ["nombre", "correo", "organizacion"]
    search_fields = ["organizacion__nombre", "nombre", "correo"]
    list_select_related = ["organizacion"]
    list_per_page = 10


@admin.register(Organization)
class OrganizationAdmin(AccionesDeFila, ModelAdmin):
    list_display = ["rut", "nombre", "rubro"]
    search_fields = ["rut", "nombre", "rubro"]
    list_per_page = 10


@admin.register(Unit)
class UnitAdmin(AccionesDeFila, FormatosDeArchivo, ModelAdmin):
    list_display = ["id", "nombre", "organizacion", "esta_vetada"]
    search_fields = ["nombre", "organizacion__nombre", "organizacion__rut"]
    list_select_related = ["organizacion"]
    list_per_page = 10


@admin.register(Member)
class MemberAdmin(AccionesDeFila, ModelAdmin):
    list_display = ["nombre", "proyecto", "es_visible"]
    search_fields = ["proyecto__titulo", "nombre"]
    list_select_related = ["proyecto"]
    list_per_page = 10
