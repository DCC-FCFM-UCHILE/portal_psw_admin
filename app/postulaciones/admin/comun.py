from django import forms
from django.core.validators import FileExtensionValidator
from django.db import models


class FormatosDeArchivo:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, models.FileField) and campo is not None:
            validadores = [validador for validador in db_field.validators if isinstance(validador, FileExtensionValidator)]
            extensiones = [f".{extension}" for validador in validadores for extension in validador.allowed_extensions or []]
            if extensiones:
                campo.widget.attrs["accept"] = ",".join(extensiones)
        return campo


class TextoConSaltos(forms.CharField):
    def to_python(self, value):
        texto = super().to_python(value)
        return texto.replace("\r\n", "\n") if texto else texto
