from django.contrib import admin
from unfold.admin import ModelAdmin

from convenios.models import RulesApplications
from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.listado import ListadoParcial


@admin.register(RulesApplications)
class RulesApplicationsAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, ModelAdmin):
    list_display = ["descripcion"]
    search_fields = ["descripcion"]
    list_per_page = 10
