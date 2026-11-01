from django import forms
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.widgets import UnfoldAdminEmailInputWidget, UnfoldAdminTextInputWidget

from postulaciones import correo


class EditorDeCorreo(WysiwygWidget):
    template_name = "postulaciones/widgets/editor_correo.html"

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        contexto["widget"]["logo"] = correo.LOGO
        return contexto


class CorreoForm(forms.Form):
    correo = forms.EmailField(label="Correo", max_length=100, widget=UnfoldAdminEmailInputWidget)
    asunto = forms.CharField(label="Asunto", max_length=100, widget=UnfoldAdminTextInputWidget)
    contenido = forms.CharField(label="Mensaje", widget=EditorDeCorreo(attrs={"aria-required": "true"}))
