from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RelatedDropdownFilter
from unfold.contrib.filters.forms import DropdownForm
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminSelectWidget

from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.listado import ListadoParcial, zona_pedida
from postulaciones import historial
from postulaciones.admin.comun import FormatosDeArchivo
from postulaciones.models import Application
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


@admin.register(Application)
class ApplicationAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, FormatosDeArchivo, ModelAdmin):
    list_display = ["titulo", "convocatoria", "organizacion", "unidad", "postulante", "mostrar_estado", "fue_notificada", "perfil"]
    list_display_links = ["titulo"]
    list_filter = ["estado", NotificacionFilter, ("convocatoria", ConvocatoriaFilter)]
    list_filter_submit = True
    search_fields = ["titulo", "unidad__nombre", "unidad__organizacion__nombre"]
    list_select_related = ["convocatoria", "postulante", "unidad__organizacion"]
    list_per_page = 10
    actions = ["aceptar", "rechazar"]
    acciones_en_listado = ("aceptar", "rechazar")
    actions_row = ["editar_fila", "aceptar_fila", "rechazar_fila", "notificar", "contactar", "eliminar_fila"]
    actions_detail = ["notificar", "contactar"]
    list_before_template = "postulaciones/admin/filtros_estado.html"
    change_form_before_template = "postulaciones/admin/resumen_postulacion.html"

    def changelist_view(self, request, extra_context=None):
        respuesta = super().changelist_view(request, extra_context)
        if hasattr(respuesta, "context_data") and "cl" in respuesta.context_data and zona_pedida(request) != "resultados-listado":
            respuesta.context_data["filtros_estado"] = self.filtros_estado(request, respuesta.context_data["cl"])
        return respuesta

    def filtros_estado(self, request, cl):
        del_estado = next(filtro.expected_parameters() for filtro in cl.filter_specs if "estado__exact" in filtro.expected_parameters())
        postulaciones = cl.get_queryset(request, exclude_parameters=del_estado)
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
            '<a href="{}" target="_blank" rel="noopener" class="enlace inline-flex min-h-6 items-center">Descargar<span class="sr-only">'
            " el perfil de {} (se abre en otra pestaña)</span></a>",
            obj.archivo.url,
            obj.titulo,
        )

    @action(description="Aceptar", permissions=["change"])
    def aceptar(self, request, queryset):
        self.resolver_lote(request, queryset, Application.Estado.ACEPTADA, historial.ACEPTADA, ("aceptó", "aceptaron"))

    @action(description="Rechazar", permissions=["change"])
    def rechazar(self, request, queryset):
        self.resolver_lote(request, queryset, Application.Estado.RECHAZADA, historial.RECHAZADA, ("rechazó", "rechazaron"))

    def resolver_lote(self, request, queryset, estado, mensaje, verbos):
        resultado = Application.Estado(estado).label.lower()
        postulaciones = list(queryset.exclude(estado=estado))
        iguales = queryset.filter(estado=estado).count()
        if not postulaciones:
            messages.info(request, f"Las postulaciones elegidas ya estaban {resultado}s; no cambió nada.")
            return
        notificadas = sum(1 for postulacion in postulaciones if postulacion.fue_notificada)
        Application.objects.filter(pk__in=[postulacion.pk for postulacion in postulaciones]).update(estado=estado, fue_notificada=False)
        historial.registrar(request, postulaciones, mensaje)
        cantidad = len(postulaciones)
        partes = [f"Se {verbos[0]} 1 postulación." if cantidad == 1 else f"Se {verbos[1]} {cantidad} postulaciones."]
        if iguales:
            partes.append(f"1 ya estaba {resultado} y no cambió." if iguales == 1 else f"{iguales} ya estaban {resultado}s y no cambiaron.")
        if notificadas:
            partes.append(
                "1 tenía la notificación enviada: hay que notificarla de nuevo."
                if notificadas == 1
                else f"{notificadas} tenían la notificación enviada: hay que notificarlas de nuevo."
            )
        messages.success(request, " ".join(partes))

    @action(description="Aceptar", url_path="aceptar-fila", permissions=["change"], icon="check_circle", attrs={"formmethod": "post"})
    def aceptar_fila(self, request, object_id):
        return self.resolver_fila(request, object_id, Application.Estado.ACEPTADA, historial.ACEPTADA)

    @action(description="Rechazar", url_path="rechazar-fila", permissions=["change"], icon="cancel", attrs={"formmethod": "post"})
    def rechazar_fila(self, request, object_id):
        return self.resolver_fila(request, object_id, Application.Estado.RECHAZADA, historial.RECHAZADA)

    def resolver_fila(self, request, object_id, estado, mensaje):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        postulacion = self.get_object(request, unquote(object_id))
        if postulacion is None:
            raise Http404
        resultado = Application.Estado(estado).label.lower()
        if postulacion.estado == estado:
            messages.info(request, f"La postulación «{postulacion}» ya estaba {resultado}.")
        else:
            Application.objects.filter(pk=postulacion.pk).update(estado=estado, fue_notificada=False)
            historial.registrar(request, [postulacion], mensaje)
            messages.success(request, f"La postulación «{postulacion}» quedó {resultado}.")
        destino = request.META.get("HTTP_REFERER", "")
        if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            destino = reverse("admin:applications_application_changelist")
        return redirect(destino)

    @action(description="Notificar", url_path="notificar", permissions=["change"], icon="mail")
    def notificar(self, request, object_id):
        return redirect("admin:applications_application_notificar_correo", pk=object_id)

    @action(description="Contactar", url_path="contactar", permissions=["change"], icon="person")
    def contactar(self, request, object_id):
        return redirect("admin:applications_application_contactar_correo", pk=object_id)
