from django.contrib import admin
from unfold.admin import ModelAdmin

from convenios.models import RulesApplications
from core.acciones import AccionesDeFila
from core.listado import ListadoParcial


@admin.register(RulesApplications)
class RulesApplicationsAdmin(ListadoParcial, AccionesDeFila, ModelAdmin):
    list_display = ["descripcion"]
    search_fields = ["descripcion"]
    list_per_page = 10
