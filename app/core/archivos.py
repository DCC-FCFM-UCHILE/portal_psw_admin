import mimetypes
import os

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404

from convenios.models import RulesApplications
from postulaciones.models import Application, Unit

DUENOS = [
    (Application, "archivo"),
    (Unit, "logo"),
    (RulesApplications, "perfil_de_proyecto"),
    (RulesApplications, "convenio_de_colaboracion"),
]

EN_EL_NAVEGADOR = {"application/pdf", "image/png", "image/jpeg"}


def puede_ver(usuario, modelo):
    opciones = modelo._meta
    return any(usuario.has_perm(f"{opciones.app_label}.{accion}_{opciones.model_name}") for accion in ("view", "change"))


def entregar(request, nombre):
    if not any(puede_ver(request.user, modelo) and modelo.objects.filter(**{campo: nombre}).exists() for modelo, campo in DUENOS):
        raise Http404
    try:
        archivo = default_storage.open(nombre)
    except (FileNotFoundError, SuspiciousFileOperation):
        raise Http404
    tipo, _ = mimetypes.guess_type(nombre)
    return FileResponse(archivo, as_attachment=tipo not in EN_EL_NAVEGADOR, filename=os.path.basename(nombre))
