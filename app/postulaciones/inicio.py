from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.urls import reverse
from django.utils import timezone

from postulaciones.models import Announcement, Application, ApprovedProject

ACCIONES = {ADDITION: "agregó", CHANGE: "modificó", DELETION: "eliminó"}


def convocatoria_actual():
    hoy = timezone.localdate()
    abierta = Announcement.objects.filter(inicio__lte=hoy, cierre__gte=hoy).first()
    return abierta, abierta or Announcement.objects.first()


def sigue_existiendo(registro):
    modelo = registro.content_type.model_class() if registro.content_type else None
    return modelo is not None and modelo._default_manager.filter(pk=registro.object_id).exists()


def actividad_reciente(cantidad=6):
    registros = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:cantidad]
    return [
        {
            "quien": registro.user.get_full_name() or registro.user.get_username(),
            "accion": ACCIONES.get(registro.action_flag, "modificó"),
            "tipo": registro.content_type.name if registro.content_type else "",
            "objeto": registro.object_repr,
            "enlace": registro.get_admin_url() if registro.action_flag != DELETION and sigue_existiendo(registro) else "",
            "cuando": registro.action_time,
        }
        for registro in registros
    ]


def indicadores(request, context):
    usuario = request.user
    abierta, convocatoria = convocatoria_actual()
    tarjetas = []

    if usuario.has_perm("applications.view_application"):
        postulaciones = reverse("admin:applications_application_changelist")
        if convocatoria:
            de_la_convocatoria = Application.objects.filter(convocatoria=convocatoria)
            filtro = f"?convocatoria__id__exact={convocatoria.pk}"
            tarjetas += [
                {
                    "etiqueta": f"Postulaciones {convocatoria}",
                    "valor": de_la_convocatoria.count(),
                    "enlace": postulaciones + filtro,
                    "icono": "assignment",
                },
                {
                    "etiqueta": "Por revisar",
                    "valor": de_la_convocatoria.filter(estado=Application.Estado.CREADA).count(),
                    "enlace": f"{postulaciones}{filtro}&estado__exact={Application.Estado.CREADA}",
                    "icono": "pending_actions",
                },
            ]
        tarjetas.append(
            {
                "etiqueta": "Resueltas sin notificar",
                "valor": Application.objects.exclude(estado=Application.Estado.CREADA).filter(fue_notificada=False).count(),
                "enlace": f"{postulaciones}?notificacion=pendiente",
                "icono": "mark_email_unread",
            }
        )

    if usuario.has_perm("applications.view_approvedproject"):
        tarjetas.append(
            {
                "etiqueta": "Proyectos sin publicar",
                "valor": ApprovedProject.objects.filter(es_visible=False).count(),
                "enlace": reverse("admin:applications_approvedproject_changelist") + "?es_visible__exact=0",
                "icono": "visibility_off",
            }
        )

    accesos = []
    if usuario.has_perm("applications.add_announcement"):
        accesos.append({"titulo": "Crear una convocatoria", "enlace": reverse("admin:applications_announcement_add"), "icono": "event"})
    if usuario.has_perm("commons.view_rulesapplications"):
        accesos.append(
            {"titulo": "Ver los convenios", "enlace": reverse("admin:commons_rulesapplications_changelist"), "icono": "description"}
        )
    if usuario.has_perm("auth.view_user"):
        accesos.append({"titulo": "Administrar usuarios", "enlace": reverse("admin:auth_user_changelist"), "icono": "person"})

    context.update(
        {
            "convocatoria_abierta": abierta,
            "convocatoria": convocatoria,
            "tarjetas": tarjetas,
            "actividad": actividad_reciente(),
            "accesos": accesos,
            "titulo_cabecera_secundario": True,
            "title": "Inicio",
        }
    )
    return context
