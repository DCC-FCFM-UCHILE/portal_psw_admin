from django.contrib.auth import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from unfold.forms import AuthenticationForm, UserChangeForm
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


class IngresoForm(AuthenticationForm):
    def describir_error(self):
        for nombre in ("username", "password"):
            self.fields[nombre].widget.attrs["aria-describedby"] = "error-ingreso"

    def get_invalid_login_error(self):
        self.describir_error()
        return super().get_invalid_login_error()

    def confirm_login_allowed(self, user):
        try:
            super().confirm_login_allowed(user)
        except ValidationError:
            self.describir_error()
            raise
