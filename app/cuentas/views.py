from django.contrib import admin, messages
from django.contrib.auth import views
from django.urls import reverse_lazy

from cuentas.forms import NuevaClaveForm, RestablecerForm


class ConSitio:
    def get_context_data(self, **kwargs):
        return {**admin.site.each_context(self.request), **super().get_context_data(**kwargs)}


class RestablecerView(ConSitio, views.PasswordResetView):
    form_class = RestablecerForm
    success_url = reverse_lazy("password_reset_done")


class RestablecerEnviadoView(ConSitio, views.PasswordResetDoneView):
    pass


class RestablecerConfirmarView(ConSitio, views.PasswordResetConfirmView):
    form_class = NuevaClaveForm
    success_url = reverse_lazy("password_reset_complete")


class RestablecerListoView(ConSitio, views.PasswordResetCompleteView):
    pass


class SalirView(views.LogoutView):
    next_page = "admin:login"

    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.success(request, "Cerraste la sesión.")
        return respuesta
