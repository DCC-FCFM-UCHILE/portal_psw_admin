from django.contrib.admin import helpers
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from unfold.admin import checkbox
from unfold.decorators import action, display


class AccionesDeFila:
    actions_row = ["editar_fila", "eliminar_fila"]

    @display(description=mark_safe(checkbox.render("action_toggle_all", 1)))
    def action_checkbox(self, obj):
        return checkbox.render(helpers.ACTION_CHECKBOX_NAME, str(obj.pk), {"aria-label": f"Seleccionar «{obj or f'registro {obj.pk}'}»"})

    @action(description="Editar", url_path="editar-fila", permissions=["change"], icon="edit")
    def editar_fila(self, request, object_id):
        return redirect(f"admin:{self.opts.app_label}_{self.opts.model_name}_change", object_id)

    @action(description="Eliminar", url_path="eliminar-fila", permissions=["delete"], icon="delete", attrs={"data-peligro": "true"})
    def eliminar_fila(self, request, object_id):
        return redirect(f"admin:{self.opts.app_label}_{self.opts.model_name}_delete", object_id)
