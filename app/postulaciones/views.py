from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import FormView
from unfold.views import UnfoldModelAdminViewMixin

from postulaciones import correo
from postulaciones.forms import CorreoForm
from postulaciones.models import Application


class CorreoPostulanteView(UnfoldModelAdminViewMixin, FormView):
    form_class = CorreoForm
    template_name = "postulaciones/correo_postulante.html"
    permission_required = "applications.change_application"
    titulos = {"notificar": "Notificar", "contactar": "Contactar"}
    exitos = {"notificar": "Notificación enviada exitosamente.", "contactar": "Correo enviado exitosamente."}
    tipo = None
    model_admin = None

    def dispatch(self, request, *args, **kwargs):
        self.postulacion = get_object_or_404(Application.objects.select_related("postulante", "unidad__organizacion"), pk=kwargs["pk"])
        self.title = f"{self.titulos[self.tipo]} · {self.postulacion}"
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        contenido = render_to_string(f"postulaciones/correo/{self.tipo}.html", {"postulacion": self.postulacion})
        return {"correo": self.postulacion.postulante.correo, "contenido": contenido}

    def get_context_data(self, **kwargs):
        ficha = reverse("admin:applications_application_change", args=[self.postulacion.pk])
        migas = {
            "ruta": [
                {"titulo": "Postulaciones", "enlace": reverse("admin:applications_application_changelist")},
                {"titulo": str(self.postulacion), "enlace": ficha},
            ],
            "titulo": self.titulos[self.tipo],
        }
        sin_resultado = self.tipo == "notificar" and self.postulacion.estado == Application.Estado.CREADA
        return super().get_context_data(
            postulacion=self.postulacion, cancelar=ficha, migas_vista=migas, sin_resultado=sin_resultado, **kwargs
        )

    def form_valid(self, form):
        if not correo.enviar(form.cleaned_data["correo"], form.cleaned_data["asunto"], form.cleaned_data["contenido"]):
            messages.error(self.request, "No se pudo enviar el correo. Inténtalo de nuevo más tarde.")
            return self.render_to_response(self.get_context_data(form=form))
        self.postulacion.fue_notificada = True
        self.postulacion.save(update_fields=["fue_notificada", "actualizada_en"])
        messages.success(self.request, self.exitos[self.tipo])
        return redirect(reverse("admin:applications_application_changelist"))

    def form_invalid(self, form):
        messages.warning(self.request, "El correo necesita destinatario, asunto y mensaje.")
        return super().form_invalid(form)
