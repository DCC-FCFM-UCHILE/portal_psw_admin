from django.contrib.admin.models import DELETION, LogEntry
from django.urls import reverse
from django.utils import timezone

from postulaciones import historial
from postulaciones.models import Announcement, Application, ApprovedProject


def convocatoria_actual():
    hoy = timezone.localdate()
    abierta = Announcement.objects.filter(inicio__lte=hoy, cierre__gte=hoy).first()
    return abierta, abierta or Announcement.objects.first()


def sigue_existiendo(registro):
    modelo = registro.content_type.model_class() if registro.content_type else None
    return modelo is not None and modelo._default_manager.filter(pk=registro.object_id).exists()


def puede_ver(usuario, registro):
    tipo = registro.content_type
    return tipo is not None and (
        usuario.has_perm(f"{tipo.app_label}.view_{tipo.model}") or usuario.has_perm(f"{tipo.app_label}.change_{tipo.model}")
    )


def actividad_reciente(usuario, cantidad=6):
    recientes = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:200]
    registros = [registro for registro in recientes if puede_ver(usuario, registro)][:cantidad]
    return [
        {
            "quien": registro.user.get_full_name() or registro.user.get_username(),
            "accion": historial.verbos(registro)[0],
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
            "actividad": actividad_reciente(usuario),
            "sin_permisos": not usuario.is_superuser and not usuario.get_all_permissions(),
            "accesos": accesos,
            "titulo_cabecera_secundario": True,
            "title": "Inicio",
        }
    )
    return context
