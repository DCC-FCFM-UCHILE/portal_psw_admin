from django.contrib import admin
from django.contrib.auth import views
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

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


@method_decorator(cache_control(public=True, max_age=31536000, immutable=True), name="dispatch")
class SiluetasView(TemplateView):
    template_name = "components/siluetas/vistas.html"

    def get(self, request, *args, **kwargs):
        respuesta = super().get(request, *args, **kwargs)
        respuesta["X-Robots-Tag"] = "noindex"
        return respuesta
