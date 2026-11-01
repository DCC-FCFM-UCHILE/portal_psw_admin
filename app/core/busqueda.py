from functools import reduce
from operator import or_

from django.contrib.admin.utils import NotRelationField, get_fields_from_path, lookup_spawns_duplicates
from django.core.exceptions import FieldDoesNotExist
from django.db.models import CharField, F, Func, Q, TextField, Value
from django.utils.text import smart_split, unescape_string_literal

CON_TILDE = "áéíóúüñÁÉÍÓÚÜÑ"
SIN_TILDE = "aeiouunAEIOUUN"


def sin_tildes(texto):
    return texto.translate(str.maketrans(CON_TILDE, SIN_TILDE))


class BusquedaSinTildes:
    def get_search_results(self, request, queryset, search_term):
        campos = [str(campo) for campo in self.get_search_fields(request)]
        if not campos or not search_term:
            return super().get_search_results(request, queryset, search_term)
        try:
            destinos = [get_fields_from_path(self.model, campo)[-1] for campo in campos]
        except (FieldDoesNotExist, NotRelationField):
            return super().get_search_results(request, queryset, search_term)
        alias = {}
        consultas = []
        for indice, (campo, destino) in enumerate(zip(campos, destinos)):
            if isinstance(destino, (CharField, TextField)):
                alias[f"busqueda_{indice}"] = Func(F(campo), Value(CON_TILDE), Value(SIN_TILDE), function="TRANSLATE", output_field=CharField())
                consultas.append((f"busqueda_{indice}__icontains", True))
            else:
                consultas.append((f"{campo}__icontains", False))
        terminos = []
        for palabra in smart_split(search_term):
            if palabra.startswith(('"', "'")) and palabra[0] == palabra[-1]:
                palabra = unescape_string_literal(palabra)
            terminos.append(reduce(or_, (Q(**{consulta: sin_tildes(palabra) if traducir else palabra}) for consulta, traducir in consultas)))
        duplicados = any(lookup_spawns_duplicates(self.opts, campo) for campo in campos)
        return queryset.alias(**alias).filter(*terminos), duplicados
