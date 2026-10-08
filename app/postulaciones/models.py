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
    nombre = models.CharField("nombre", max_length=200, blank=True, null=True, db_column="name")
    rubro = models.CharField("rubro o giro", max_length=50, blank=True, null=True, db_column="organization_line")

    class Meta:
        managed = False
        db_table = "applications_organization"
        verbose_name = "organización"
        verbose_name_plural = "organizaciones"

    def __str__(self):
        return self.nombre or self.rut


class Candidate(Auditada):
    organizacion = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="postulantes", db_column="organization_id", verbose_name="organización"
    )
    correo = models.EmailField("correo", max_length=50, db_column="email")
    nombre = models.CharField("nombre", max_length=100, blank=True, null=True, db_column="names")

    class Meta:
        managed = False
        db_table = "applications_candidate"
        verbose_name = "postulante"
        verbose_name_plural = "postulantes"

    def __str__(self):
        return self.nombre or self.correo


class Announcement(Auditada):
    convenio = models.ForeignKey(
        "commons.RulesApplications",
        on_delete=models.PROTECT,
        related_name="convocatorias",
        db_column="rules_id",
        verbose_name="formato de postulación",
    )
    inicio = models.DateField("inicio", db_column="start")
    cierre = models.DateField("cierre", db_column="end")
    semestre = models.CharField("semestre", max_length=2, choices=Semestre.choices, db_column="semester")
    anio = models.PositiveIntegerField("año", default=anio_actual, db_column="year")

    class Meta:
        managed = False
        db_table = "applications_announcement"
        verbose_name = "convocatoria"
        verbose_name_plural = "convocatorias"
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
    nombre = models.CharField("nombre", max_length=200, blank=True, null=True, db_column="name")
    logo = models.FileField("logo", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=["png", "jpg", "svg"])])
    esta_vetada = models.BooleanField("está vetada", default=False, db_column="is_veto")
    organizacion = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="unidades",
        db_column="organization_id",
        blank=True,
        null=True,
        verbose_name="organización",
    )

    class Meta:
        managed = False
        db_table = "applications_unit"
        verbose_name = "unidad"
        verbose_name_plural = "unidades"

    def __str__(self):
        return self.nombre or ""


class Application(Auditada):
    class Estado(models.TextChoices):
        CREADA = "CR", "Creada"
        RECHAZADA = "RE", "Rechazada"
        ACEPTADA = "AC", "Aceptada"

    postulante = models.ForeignKey(
        Candidate, on_delete=models.PROTECT, related_name="postulaciones", db_column="candidate_id", verbose_name="postulante"
    )
    convocatoria = models.ForeignKey(
        Announcement, on_delete=models.PROTECT, related_name="postulaciones", db_column="announcement_id", verbose_name="convocatoria"
    )
    unidad = models.ForeignKey(
        Unit, on_delete=models.PROTECT, related_name="postulaciones", db_column="unit_id", null=True, verbose_name="unidad"
    )
    titulo = models.CharField("título", max_length=100, db_column="title")
    descripcion = models.CharField("descripción", max_length=200, blank=True, null=True, db_column="short_description")
    archivo = models.FileField("perfil de proyecto", db_column="file", validators=[FileExtensionValidator(allowed_extensions=["pdf"])])
    estado = models.CharField("estado", max_length=2, choices=Estado.choices, default=Estado.CREADA, db_column="status")
    fue_notificada = models.BooleanField("notificada", default=False, db_column="is_notified")

    class Meta:
        managed = False
        db_table = "applications_application"
        verbose_name = "postulación"
        verbose_name_plural = "postulaciones"
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
        verbose_name="postulación",
    )
    titulo = models.CharField("título", max_length=100, db_column="title")
    descripcion = models.TextField("descripción", blank=True, null=True, db_column="description")
    semestre = models.CharField("semestre", max_length=2, choices=Semestre.choices, db_column="semester")
    anio = models.PositiveIntegerField("año", default=anio_actual, db_column="year")
    tutor = models.CharField("auxiliar", max_length=100, db_column="aux")
    es_visible = models.BooleanField("visible", default=False, db_column="is_visible")

    class Meta:
        managed = False
        db_table = "applications_approvedproject"
        verbose_name = "proyecto"
        verbose_name_plural = "proyectos"
        ordering = ["-postulacion__convocatoria__cierre", "-id"]

    def __str__(self):
        return self.titulo


class Member(Auditada):
    proyecto = models.ForeignKey(
        ApprovedProject, on_delete=models.PROTECT, related_name="integrantes", db_column="project_id", verbose_name="proyecto"
    )
    nombre = models.CharField("nombre", max_length=100, db_column="name")
    es_visible = models.BooleanField("visible", default=False, db_column="is_visible")

    class Meta:
        managed = False
        db_table = "applications_member"
        verbose_name = "integrante"
        verbose_name_plural = "integrantes"

    def __str__(self):
        return self.nombre
