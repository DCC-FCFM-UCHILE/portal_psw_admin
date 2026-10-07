from django.contrib import admin
from django.contrib.auth import views
from django.urls import reverse_lazy


class ConSitio:
    def get_context_data(self, **kwargs):
        return {**admin.site.each_context(self.request), **super().get_context_data(**kwargs)}


class RestablecerView(ConSitio, views.PasswordResetView):
    success_url = reverse_lazy("password_reset_done")


class RestablecerEnviadoView(ConSitio, views.PasswordResetDoneView):
    pass


class RestablecerConfirmarView(ConSitio, views.PasswordResetConfirmView):
    success_url = reverse_lazy("password_reset_complete")


class RestablecerListoView(ConSitio, views.PasswordResetCompleteView):
    pass
