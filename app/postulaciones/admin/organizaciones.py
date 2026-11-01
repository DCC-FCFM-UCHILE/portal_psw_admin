from django.contrib import admin
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin

from core.acciones import AccionesDeFila
from core.busqueda import BusquedaSinTildes
from core.ficha import SinGuardarYAgregarOtro
from core.listado import ListadoParcial
from postulaciones.admin.comun import FormatosDeArchivo
from postulaciones.models import Candidate, Organization, Unit


def logo_png_o_jpg(archivo):
    extension = archivo.name.rsplit(".", 1)[-1].lower()
    inicio = archivo.read(4)
    archivo.seek(0)
    if extension not in {"png", "jpg", "jpeg"} or not inicio.startswith((b"\x89PNG", b"\xff\xd8\xff")):
        raise ValidationError("El logo tiene que ser una imagen PNG o JPG.")


@admin.register(Candidate)
class CandidateAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, ModelAdmin):
    list_display = ["nombre", "correo", "organizacion"]
    search_fields = ["organizacion__nombre", "nombre", "correo"]
    list_select_related = ["organizacion"]
    list_per_page = 10


@admin.register(Organization)
class OrganizationAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, ModelAdmin):
    list_display = ["rut", "nombre", "rubro"]
    search_fields = ["rut", "nombre", "rubro"]
    list_per_page = 10


@admin.register(Unit)
class UnitAdmin(BusquedaSinTildes, ListadoParcial, AccionesDeFila, SinGuardarYAgregarOtro, FormatosDeArchivo, ModelAdmin):
    list_display = ["id", "nombre", "organizacion", "esta_vetada"]
    search_fields = ["nombre", "organizacion__nombre", "organizacion__rut"]
    list_select_related = ["organizacion"]
    list_per_page = 10

    def get_form(self, request, obj=None, change=False, **kwargs):
        formulario = super().get_form(request, obj, change, **kwargs)
        formulario.base_fields["nombre"].required = True
        logo = formulario.base_fields["logo"]
        logo.validators.append(logo_png_o_jpg)
        logo.widget.attrs["accept"] = ".png,.jpg,.jpeg"
        return formulario
