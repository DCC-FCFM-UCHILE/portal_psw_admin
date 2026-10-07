from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from convenios.models import Auditada


def anio_actual():
    return timezone.localdate().year


class Semestre(models.TextChoices):
    OTONO = "FA", "Otoño"
    PRIMAVERA = "SP", "Primavera"


class Organization(Auditada):
    rut = models.CharField("RUT", max_length=50)
    nombre = models.CharField("Nombre", max_length=200, blank=True, null=True, db_column="name")
    rubro = models.CharField("Rubro o giro", max_length=50, blank=True, null=True, db_column="organization_line")

    class Meta:
        managed = False
        db_table = "applications_organization"
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"

    def __str__(self):
        return self.nombre or self.rut


class Candidate(Auditada):
    organizacion = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="postulantes", db_column="organization_id", verbose_name="Organización"
    )
    correo = models.EmailField("Correo", max_length=50, db_column="email")
    nombre = models.CharField("Nombre", max_length=100, blank=True, null=True, db_column="names")

    class Meta:
        managed = False
        db_table = "applications_candidate"
        verbose_name = "Postulante"
        verbose_name_plural = "Postulantes"

    def __str__(self):
        return self.nombre or self.correo


class Announcement(Auditada):
    convenio = models.ForeignKey(
        "commons.RulesApplications",
        on_delete=models.PROTECT,
        related_name="convocatorias",
        db_column="rules_id",
        verbose_name="Formato de postulación",
    )
    inicio = models.DateField("Inicio", db_column="start")
    cierre = models.DateField("Cierre", db_column="end")
    semestre = models.CharField("Semestre", max_length=2, choices=Semestre.choices, db_column="semester")
    anio = models.PositiveIntegerField("Año", default=anio_actual, db_column="year")

    class Meta:
        managed = False
        db_table = "applications_announcement"
        verbose_name = "Convocatoria"
        verbose_name_plural = "Convocatorias"
        ordering = ["-cierre"]

    def __str__(self):
        return f"{self.anio} {self.get_semestre_display()}"

    def clean(self):
        if self.inicio is None or self.cierre is None:
            return
        if self.cierre < self.inicio:
            raise ValidationError("La fecha de inicio debe ser menor a la final")
        cruzadas = Announcement.objects.filter(inicio__lte=self.cierre, cierre__gte=self.inicio).exclude(pk=self.pk)
        if cruzadas.exists():
            raise ValidationError("Ya existe un periodo entre las fechas seleccionadas")


class Unit(Auditada):
    nombre = models.CharField("Nombre", max_length=200, blank=True, null=True, db_column="name")
    logo = models.FileField("Logo", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=["png", "jpg", "svg"])])
    esta_vetada = models.BooleanField("Está vetada", default=False, db_column="is_veto")
    organizacion = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="unidades",
        db_column="organization_id",
        blank=True,
        null=True,
        verbose_name="Organización",
    )

    class Meta:
        managed = False
        db_table = "applications_unit"
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"

    def __str__(self):
        return self.nombre or ""


class Application(Auditada):
    class Estado(models.TextChoices):
        CREADA = "CR", "Creada"
        RECHAZADA = "RE", "Rechazada"
        ACEPTADA = "AC", "Aceptada"

    postulante = models.ForeignKey(
        Candidate, on_delete=models.PROTECT, related_name="postulaciones", db_column="candidate_id", verbose_name="Postulante"
    )
    convocatoria = models.ForeignKey(
        Announcement, on_delete=models.PROTECT, related_name="postulaciones", db_column="announcement_id", verbose_name="Convocatoria"
    )
    unidad = models.ForeignKey(
        Unit, on_delete=models.PROTECT, related_name="postulaciones", db_column="unit_id", null=True, verbose_name="Unidad"
    )
    titulo = models.CharField("Título", max_length=100, db_column="title")
    descripcion = models.CharField("Descripción", max_length=200, blank=True, null=True, db_column="short_description")
    archivo = models.FileField("Perfil de proyecto", db_column="file", validators=[FileExtensionValidator(allowed_extensions=["pdf"])])
    estado = models.CharField("Estado", max_length=2, choices=Estado.choices, default=Estado.CREADA, db_column="status")
    fue_notificada = models.BooleanField("Notificada", default=False, db_column="is_notified")

    class Meta:
        managed = False
        db_table = "applications_application"
        verbose_name = "Postulación"
        verbose_name_plural = "Postulaciones"
        ordering = ["-id"]

    def __str__(self):
        return self.titulo

    @property
    def organizacion(self):
        return self.unidad.organizacion if self.unidad else None


class ApprovedProject(Auditada):
    postulacion = models.OneToOneField(
        Application,
        on_delete=models.PROTECT,
        related_name="proyecto",
        db_column="application_id",
        blank=True,
        null=True,
        verbose_name="Postulación",
    )
    titulo = models.CharField("Título", max_length=100, db_column="title")
    descripcion = models.TextField("Descripción", blank=True, null=True, db_column="description")
    semestre = models.CharField("Semestre", max_length=2, choices=Semestre.choices, db_column="semester")
    anio = models.PositiveIntegerField("Año", default=anio_actual, db_column="year")
    tutor = models.CharField("Auxiliar", max_length=100, db_column="aux")
    es_visible = models.BooleanField("Visible", default=False, db_column="is_visible")

    class Meta:
        managed = False
        db_table = "applications_approvedproject"
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ["-postulacion__convocatoria__cierre", "-id"]

    def __str__(self):
        return self.titulo


class Member(Auditada):
    proyecto = models.ForeignKey(
        ApprovedProject, on_delete=models.PROTECT, related_name="integrantes", db_column="project_id", verbose_name="Proyecto"
    )
    nombre = models.CharField("Nombre", max_length=100, db_column="name")
    es_visible = models.BooleanField("Visible", default=False, db_column="is_visible")

    class Meta:
        managed = False
        db_table = "applications_member"
        verbose_name = "Integrante"
        verbose_name_plural = "Integrantes"

    def __str__(self):
        return self.nombre
