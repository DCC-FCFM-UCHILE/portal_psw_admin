from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path

from core.rutas import redirigir_antigua, traducir
from cuentas import views

urlpatterns = [
    re_path(r"^admin/(?P<antigua>.*)$", redirigir_antigua),
    re_path(r"^reset/(?P<antigua>.*)$", redirigir_antigua, {"prefijo": "reset/"}),
    path("recuperar-contrasena/", views.RestablecerView.as_view(), name="admin_password_reset"),
    path("recuperar-contrasena/enviado/", views.RestablecerEnviadoView.as_view(), name="password_reset_done"),
    path("recuperar-contrasena/listo/", views.RestablecerListoView.as_view(), name="password_reset_complete"),
    path("recuperar-contrasena/<uidb64>/<token>/", views.RestablecerConfirmarView.as_view(), name="password_reset_confirm"),
    path("siluetas/", views.SiluetasView.as_view(), name="siluetas"),
    path("salir/", views.SalirView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("", (traducir(admin.site.get_urls()), "admin", admin.site.name)),
]
