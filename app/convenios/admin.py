from django.contrib import admin
from unfold.admin import ModelAdmin

from convenios.models import RulesApplications


@admin.register(RulesApplications)
class RulesApplicationsAdmin(ModelAdmin):
    list_display = ["descripcion"]
    search_fields = ["descripcion"]
    list_per_page = 10
