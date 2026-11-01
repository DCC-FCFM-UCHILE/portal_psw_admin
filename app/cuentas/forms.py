from django.contrib.auth import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from unfold.forms import AdminOwnPasswordChangeForm, AdminPasswordChangeForm, AuthenticationForm, UserChangeForm, UserCreationForm
from unfold.widgets import BASE_INPUT_CLASSES

from cuentas.requisitos import CODIGOS, NO_CUMPLE, requisitos
from cuentas.widgets import AccesoAContrasena


class ConClasesDeUnfold:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = " ".join(BASE_INPUT_CLASSES)


class ErroresEnLaPrimeraClave:
    def validate_password_for_user(self, user, password_field_name="password2", **kwargs):
        super().validate_password_for_user(user, password_field_name=password_field_name.removesuffix("2") + "1", **kwargs)


class SinAutofocoConErrores:
    def full_clean(self):
        super().full_clean()
        if self.errors:
            for campo in self.fields.values():
                campo.widget.attrs.pop("autofocus", None)


class ConRequisitos:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mostrar_requisitos(requisitos())

    def mostrar_requisitos(self, lista):
        obligatorio = self.fields[self.clave_nueva].error_messages["required"]
        ayuda = render_to_string("cuentas/requisitos.html", {"requisitos": lista, "no_cumple": NO_CUMPLE, "obligatorio": obligatorio})
        self.fields[self.clave_nueva].help_text = ayuda
        if self.clave_nueva in self._bound_fields_cache:
            self._bound_fields_cache[self.clave_nueva].help_text = ayuda

    def full_clean(self):
        super().full_clean()
        errores = self._errors.get(self.clave_nueva) if self._errors else None
        if errores and any(error.code in CODIGOS for error in errores.as_data()):
            self._errors[self.clave_nueva] = self.error_class(
                [ValidationError(NO_CUMPLE, code="requisitos")], renderer=self.renderer, field_id=self[self.clave_nueva].auto_id
            )
            self.mostrar_requisitos(requisitos(self.data.get(self.clave_nueva, ""), self.usuario_de_la_clave()))

    @property
    def clave_nueva(self):
        return "new_password1" if "new_password1" in self.fields else "password1"

    def usuario_de_la_clave(self):
        if hasattr(self, "user"):
            return self.user
        usuario = self.instance
        setattr(usuario, usuario.USERNAME_FIELD, self.data.get(usuario.USERNAME_FIELD, ""))
        return usuario

    def requisitos(self):
        return {
            requisito["clave"]: requisito["cumple"]
            for requisito in requisitos(self.data.get(self.clave_nueva, ""), self.usuario_de_la_clave())
        }


class RestablecerForm(ConClasesDeUnfold, forms.PasswordResetForm):
    pass


class NuevaClaveForm(ConRequisitos, SinAutofocoConErrores, ErroresEnLaPrimeraClave, ConClasesDeUnfold, forms.SetPasswordForm):
    pass


class AltaUsuarioForm(ConRequisitos, SinAutofocoConErrores, ErroresEnLaPrimeraClave, UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sin_clave = self.is_bound and self.data.get("usable_password") == "false"
        for nombre in ("password1", "password2"):
            self.fields[nombre].required = not sin_clave


class CambioClaveForm(ConRequisitos, SinAutofocoConErrores, ErroresEnLaPrimeraClave, AdminPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("usable_password", None)
        for nombre in ("password1", "password2"):
            self.fields[nombre].required = True


class CambioClavePropiaForm(ConRequisitos, SinAutofocoConErrores, ErroresEnLaPrimeraClave, AdminOwnPasswordChangeForm):
    pass


class FichaUsuarioForm(UserChangeForm):
    cambia_contrasena = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        contrasena = self.fields.get("password")
        if contrasena and self.instance.pk:
            contrasena.help_text = ""
            enlace = reverse("admin:auth_user_password_change", args=[self.instance.pk]) if self.cambia_contrasena else None
            contrasena.widget = AccesoAContrasena(enlace)


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
