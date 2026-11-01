from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.ficha import SinGuardarYAgregarOtro
from core.listado import ListadoParcial
from postulaciones.models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, ModelAdmin):
    list_display = ["__str__", "inicio", "cierre", "convenio", "ver_postulaciones"]
    search_fields = ["anio"]
    list_per_page = 10

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, models.DateField) and campo is not None and not campo.help_text:
            campo.help_text = "Día/mes/año, por ejemplo 15/03/2027."
        return campo

    @display(description="Postulaciones")
    def ver_postulaciones(self, obj):
        url = reverse("admin:applications_application_changelist")
        return format_html('<a href="{}?convocatoria__id__exact={}" class="enlace">Ver postulaciones</a>', url, obj.pk)
