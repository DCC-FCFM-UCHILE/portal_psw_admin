from django.db import models


class Auditada(models.Model):
    creada_en = models.DateTimeField(auto_now_add=True, db_column="created_at")
    actualizada_en = models.DateTimeField(auto_now=True, db_column="updated_at")

    class Meta:
        abstract = True


class RulesApplications(Auditada):
    descripcion = models.CharField("descripción", max_length=200, db_column="short_description")
    perfil_de_proyecto = models.FileField("perfil de proyecto", db_column="document")
    convenio_de_colaboracion = models.FileField("convenio de colaboración", db_column="deal")

    class Meta:
        managed = False
        db_table = "commons_rulesapplications"
        verbose_name = "convenio"
        verbose_name_plural = "convenios"

    def __str__(self):
        return self.descripcion
