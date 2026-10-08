from django.contrib.auth import forms
from unfold.widgets import BASE_INPUT_CLASSES


class ConClasesDeUnfold:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = " ".join(BASE_INPUT_CLASSES)


class RestablecerForm(ConClasesDeUnfold, forms.PasswordResetForm):
    pass


class NuevaClaveForm(ConClasesDeUnfold, forms.SetPasswordForm):
    pass
