from django.forms import BoundField
from django.forms.renderers import TemplatesSetting


class CampoConErrorPrimero(BoundField):
    @property
    def aria_describedby(self):
        descripciones = super().aria_describedby
        if not descripciones:
            return descripciones
        return " ".join(sorted(descripciones.split(), key=lambda descripcion: not descripcion.endswith("_error")))


class Renderizador(TemplatesSetting):
    bound_field_class = CampoConErrorPrimero
