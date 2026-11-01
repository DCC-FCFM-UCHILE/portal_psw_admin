from django.contrib.auth import forms
from django.urls import reverse
from unfold.forms import UserChangeForm
from unfold.widgets import BASE_INPUT_CLASSES

from cuentas.widgets import AccesoAContrasena


class ConClasesDeUnfold:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = " ".join(BASE_INPUT_CLASSES)


class RestablecerForm(ConClasesDeUnfold, forms.PasswordResetForm):
    pass


class NuevaClaveForm(ConClasesDeUnfold, forms.SetPasswordForm):
    pass


class FichaUsuarioForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        contrasena = self.fields.get("password")
        if contrasena and self.instance.pk:
            contrasena.help_text = ""
            contrasena.widget = AccesoAContrasena(reverse("admin:auth_user_password_change", args=[self.instance.pk]))
