from django import forms
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.widgets import UnfoldAdminEmailInputWidget, UnfoldAdminTextInputWidget


class CorreoForm(forms.Form):
    correo = forms.EmailField(label="Correo", max_length=100, widget=UnfoldAdminEmailInputWidget)
    asunto = forms.CharField(label="Asunto", max_length=100, widget=UnfoldAdminTextInputWidget)
    contenido = forms.CharField(label="Mensaje", widget=WysiwygWidget)
