from django.apps import AppConfig


class PostulacionesConfig(AppConfig):
    name = "postulaciones"
    label = "applications"
    verbose_name = "Postulaciones"

    def ready(self):
        from postulaciones import senales  # noqa: F401
