from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry

ACEPTADA = "Aceptada."
RECHAZADA = "Rechazada."
NOTIFICADA = "Notificada por correo"
CONTACTADA = "Contactada por correo"

VERBOS = {
    ACEPTADA: ("aceptó", "la aceptó"),
    RECHAZADA: ("rechazó", "la rechazó"),
    NOTIFICADA: ("notificó", "la notificó"),
    CONTACTADA: ("escribió al postulante de", "le escribió al postulante"),
}
GENERICOS = {ADDITION: ("agregó", "la agregó"), CHANGE: ("modificó", "la modificó"), DELETION: ("eliminó", "la eliminó")}


def registrar(request, postulaciones, mensaje):
    LogEntry.objects.log_actions(user_id=request.user.pk, queryset=postulaciones, action_flag=CHANGE, change_message=mensaje)


def verbos(registro):
    for inicio, par in VERBOS.items():
        if registro.change_message.startswith(inicio):
            return par
    return GENERICOS.get(registro.action_flag, GENERICOS[CHANGE])
