from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from cuentas import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="admin:index")),
    path("admin/password_reset/", views.RestablecerView.as_view(), name="admin_password_reset"),
    path("admin/password_reset/done/", views.RestablecerEnviadoView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.RestablecerConfirmarView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.RestablecerListoView.as_view(), name="password_reset_complete"),
    path("admin/siluetas/", views.SiluetasView.as_view(), name="siluetas"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
