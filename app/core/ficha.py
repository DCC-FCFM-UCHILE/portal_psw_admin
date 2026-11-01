class SinGuardarYAgregarOtro:
    def render_change_form(self, request, context, *args, **kwargs):
        return super().render_change_form(request, {**context, "show_save_and_add_another": False}, *args, **kwargs)
