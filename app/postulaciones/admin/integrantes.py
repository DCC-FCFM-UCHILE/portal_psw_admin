from django.contrib import admin
from unfold.admin import ModelAdmin

from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.ficha import SinGuardarYAgregarOtro
from core.listado import ListadoParcial
from postulaciones.models import Member


@admin.register(Member)
class MemberAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, ModelAdmin):
    list_display = ["nombre", "proyecto", "es_visible"]
    search_fields = ["proyecto__titulo", "nombre"]
    list_select_related = ["proyecto"]
    list_per_page = 10
