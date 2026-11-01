from django.contrib import admin
from django.urls import path, re_path
from django.utils import timezone
from django.views.decorators.cache import cache_control
from django.views.decorators.http import last_modified

from core.archivos import entregar
from core.rutas import redirigir_antigua, traducir
from cuentas import views
from interfaz.views import SiluetasView

ARRANQUE = timezone.now()

catalogo = cache_control(private=True, max_age=3600)(last_modified(lambda request, **kwargs: ARRANQUE)(admin.site.i18n_javascript))

urlpatterns = [
    re_path(r"^admin/(?P<antigua>.*)$", redirigir_antigua),
    re_path(r"^reset/(?P<antigua>.*)$", redirigir_antigua, {"prefijo": "reset/"}),
    path("recuperar-contrasena/", views.RestablecerView.as_view(), name="admin_password_reset"),
    path("recuperar-contrasena/enviado/", views.RestablecerEnviadoView.as_view(), name="password_reset_done"),
    path("recuperar-contrasena/listo/", views.RestablecerListoView.as_view(), name="password_reset_complete"),
    path("recuperar-contrasena/<uidb64>/<token>/", views.RestablecerConfirmarView.as_view(), name="password_reset_confirm"),
    path("siluetas/", SiluetasView.as_view(), name="siluetas"),
    path("salir/", views.SalirView.as_view()),
    path("cambiar-contrasena/", admin.site.admin_view(views.CambiarClaveView.as_view())),
    path("sesion/", views.SesionView.as_view(), name="sesion"),
    path("jsi18n/", admin.site.admin_view(catalogo, cacheable=True)),
    path("archivos/<path:nombre>", admin.site.admin_view(entregar), name="archivo"),
]

urlpatterns += [
    path("", (traducir(admin.site.get_urls()), "admin", admin.site.name)),
]
