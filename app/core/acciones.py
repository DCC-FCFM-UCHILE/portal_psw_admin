from django.shortcuts import redirect
from unfold.decorators import action


class AccionesDeFila:
    actions_row = ["editar_fila", "eliminar_fila"]

    @action(description="Editar", url_path="editar-fila", permissions=["change"], icon="edit")
    def editar_fila(self, request, object_id):
        return redirect(f"admin:{self.opts.app_label}_{self.opts.model_name}_change", object_id)

    @action(description="Eliminar", url_path="eliminar-fila", permissions=["delete"], icon="delete", attrs={"data-peligro": "true"})
    def eliminar_fila(self, request, object_id):
        return redirect(f"admin:{self.opts.app_label}_{self.opts.model_name}_delete", object_id)
