from django.db.models.signals import post_save
from django.dispatch import receiver

from postulaciones.models import Application, ApprovedProject


@receiver(post_save, sender=Application)
def crear_proyecto_al_aceptar(sender, instance, **kwargs):
    if instance.estado != Application.Estado.ACEPTADA:
        return
    datos = {
        "titulo": instance.titulo,
        "descripcion": instance.descripcion,
        "semestre": instance.convocatoria.semestre,
        "anio": instance.convocatoria.anio,
    }
    proyecto, creado = ApprovedProject.objects.get_or_create(postulacion=instance, defaults=datos | {"tutor": ""})
    if not creado and not proyecto.es_visible:
        for campo, valor in datos.items():
            setattr(proyecto, campo, valor)
        proyecto.save(update_fields=[*datos, "actualizada_en"])
