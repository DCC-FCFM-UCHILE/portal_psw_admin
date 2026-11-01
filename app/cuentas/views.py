from django.contrib import admin, messages
from django.contrib.auth import views
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from cuentas.forms import CambioClavePropiaForm, NuevaClaveForm, RestablecerForm
from cuentas.sesion import en_milisegundos, renovar


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


class CambiarClaveView(ConSitio, views.PasswordChangeView):
    form_class = CambioClavePropiaForm
    success_url = reverse_lazy("admin:password_change_done")

    def dispatch(self, request, *args, **kwargs):
        request.current_app = admin.site.name
        return super().dispatch(request, *args, **kwargs)


class SalirView(views.LogoutView):
    next_page = "admin:login"

    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.success(request, "Cerraste la sesión.")
        return respuesta


@method_decorator(never_cache, name="dispatch")
class SesionView(View):
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_active and request.user.is_staff):
            return JsonResponse({"vence": None}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return JsonResponse({"vence": en_milisegundos(request.session)})

    def post(self, request):
        renovar(request.session)
        return self.get(request)
