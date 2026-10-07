from django.db.models.signals import post_save
from django.dispatch import receiver

from postulaciones.models import Application, ApprovedProject


@receiver(post_save, sender=Application)
def crear_proyecto_al_aceptar(sender, instance, **kwargs):
    if instance.estado != Application.Estado.ACEPTADA:
        return
    proyecto, creado = ApprovedProject.objects.get_or_create(postulacion=instance)
    if creado or not proyecto.es_visible:
        proyecto.titulo = instance.titulo
        proyecto.descripcion = instance.descripcion
        proyecto.semestre = instance.convocatoria.semestre
        proyecto.anio = instance.convocatoria.anio
        proyecto.save()
