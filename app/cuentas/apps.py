from django.apps import AppConfig


class CuentasConfig(AppConfig):
    name = "cuentas"
    verbose_name = "Cuentas"

    def ready(self):
        from django.contrib.auth.signals import user_logged_in

        from cuentas.sesion import renovar

        user_logged_in.connect(lambda request, **kwargs: renovar(request.session), weak=False, dispatch_uid="cuentas_renovar_sesion")
