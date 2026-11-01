from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView


@method_decorator(cache_control(public=True, max_age=31536000, immutable=True), name="dispatch")
class SiluetasView(TemplateView):
    template_name = "components/siluetas/vistas.html"

    def get(self, request, *args, **kwargs):
        respuesta = super().get(request, *args, **kwargs)
        respuesta["X-Robots-Tag"] = "noindex"
        return respuesta
