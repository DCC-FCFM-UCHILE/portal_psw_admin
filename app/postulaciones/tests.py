import datetime
from types import SimpleNamespace
from unittest import mock

from django.contrib import admin
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from convenios.models import RulesApplications
from cuentas.forms import NuevaClaveForm, RestablecerForm
from cuentas.templatetags.interfaz import paginas_cercanas
from postulaciones import correo, tablas_compartidas
from postulaciones.models import Announcement, Application, ApprovedProject, Candidate, Member, Organization, Unit


@override_settings(MEDIA_ROOT="/tmp/admin-pruebas-media")
class BaseCompartida(TestCase):
    @classmethod
    def setUpClass(cls):
        tablas_compartidas.crear()
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.docente = User.objects.create_superuser("docente", "docente@dcc.uchile.cl", "clave-de-prueba")
        convenio = RulesApplications.objects.create(
            descripcion="Formato 2026", perfil_de_proyecto="perfil.docx", convenio_de_colaboracion="convenio.pdf"
        )
        cls.convocatoria = Announcement.objects.create(
            convenio=convenio, inicio=datetime.date(2026, 7, 1), cierre=datetime.date(2026, 8, 31), semestre="SP", anio=2026
        )
        organizacion = Organization.objects.create(rut="76.123.456-7", nombre="Fundación Ejemplo")
        unidad = Unit.objects.create(nombre="Fundación Ejemplo", organizacion=organizacion)
        postulante = Candidate.objects.create(organizacion=organizacion, correo="ana@ejemplo.cl", nombre="Ana Pérez")
        cls.postulacion = Application.objects.create(
            postulante=postulante,
            convocatoria=cls.convocatoria,
            unidad=unidad,
            titulo="Sistema de riego",
            archivo=SimpleUploadedFile("perfil.pdf", b"%PDF-1.4"),
        )

    def setUp(self):
        self.client.force_login(self.docente)


class ListadoTests(BaseCompartida):
    def test_muestra_la_postulacion_con_su_estado(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, "Sistema de riego")
        self.assertContains(respuesta, "Creada")
        self.assertContains(respuesta, "Fundación Ejemplo")

    def test_filtra_por_convocatoria(self):
        url = reverse("admin:applications_application_changelist")
        respuesta = self.client.get(url, {"convocatoria__id__exact": self.convocatoria.pk})
        self.assertContains(respuesta, "Sistema de riego")

    def test_todas_las_vistas_del_menu_responden(self):
        for modelo in ["application", "organization", "unit", "candidate", "approvedproject", "member", "announcement"]:
            with self.subTest(modelo=modelo):
                self.assertEqual(self.client.get(reverse(f"admin:applications_{modelo}_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:commons_rulesapplications_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:applications_application_change", args=[self.postulacion.pk])).status_code, 200)

    def test_grupos_no_esta_en_la_navegacion(self):
        lista = reverse("admin:auth_group_changelist")
        self.assertNotContains(self.client.get(reverse("admin:index")), f'href="{lista}"')
        self.assertNotContains(self.client.get(reverse("admin:search"), {"s": "grup"}), f'href="{lista}"')
        Group.objects.create(name="Administradora")
        self.assertNotContains(self.client.get(reverse("admin:search"), {"s": "administradora"}), "Administradora")
        self.assertEqual(self.client.get(lista).status_code, 200)

    def test_el_listado_nombra_lo_que_agrega(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"))
        self.assertContains(respuesta, f'href="{reverse("admin:applications_organization_add")}"')
        self.assertContains(respuesta, '>Agregar <span class="max-lg:sr-only">organización</span></span>')

    def test_la_alta_no_se_enlaza_a_si_misma(self):
        alta = reverse("admin:applications_organization_add")
        self.assertNotContains(self.client.get(alta), f'href="{alta}"')

    def test_ofrece_borrar_varias_postulaciones(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, 'data-accion="delete_selected"')

    def test_los_buscadores_no_muestran_atajos_de_teclado(self):
        for url in [reverse("admin:index"), reverse("admin:applications_application_changelist")]:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "<kbd")

    def test_el_buscador_del_listado_ocupa_el_ancho_disponible(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"))
        self.assertContains(respuesta, '<div id="toolbar" class="sm:grow lg:grow-0">')

    def test_la_actividad_no_enlaza_registros_borrados(self):
        borrada = Organization.objects.create(rut="1-9", nombre="Organización borrada")
        for objeto in [borrada, self.postulacion]:
            LogEntry.objects.create(
                user=self.docente,
                content_type=ContentType.objects.get_for_model(objeto),
                object_id=str(objeto.pk),
                object_repr=str(objeto),
                action_flag=ADDITION,
            )
        enlace_borrada = reverse("admin:applications_organization_change", args=[borrada.pk])
        borrada.delete()
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, "Organización borrada")
        self.assertNotContains(respuesta, f'href="{enlace_borrada}"')
        self.assertContains(respuesta, f'href="{reverse("admin:applications_application_change", args=[self.postulacion.pk])}"')


class AccionesTests(BaseCompartida):
    def aplicar(self, accion):
        return self.client.post(
            reverse("admin:applications_application_changelist"),
            {"action": accion, "_selected_action": [self.postulacion.pk]},
            follow=True,
        )

    def test_aceptar(self):
        Application.objects.filter(pk=self.postulacion.pk).update(fue_notificada=True)
        respuesta = self.aplicar("aceptar")
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.ACEPTADA)
        self.assertFalse(self.postulacion.fue_notificada)
        self.assertContains(respuesta, "Se aceptó 1 postulación. 1 tenía la notificación enviada: hay que notificarla de nuevo.")

    def test_rechazar(self):
        self.aplicar("rechazar")
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.RECHAZADA)

    def test_la_accion_no_crea_el_proyecto(self):
        self.aplicar("aceptar")
        self.assertFalse(ApprovedProject.objects.exists())

    def test_sin_permiso_de_cambio_no_acepta(self):
        lector = User.objects.create_user("lector", password="clave-de-prueba", is_staff=True)
        lector.user_permissions.add(Permission.objects.get(codename="view_application"))
        self.client.force_login(lector)
        self.aplicar("aceptar")
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.CREADA)


class SenalTests(BaseCompartida):
    def test_guardar_aceptada_crea_el_proyecto_con_sus_datos(self):
        self.postulacion.estado = Application.Estado.ACEPTADA
        self.postulacion.save()
        proyecto = ApprovedProject.objects.get(postulacion=self.postulacion)
        self.assertEqual(proyecto.titulo, "Sistema de riego")
        self.assertEqual((proyecto.semestre, proyecto.anio), ("SP", 2026))
        self.assertFalse(proyecto.es_visible)

    def test_un_proyecto_visible_no_se_sobrescribe(self):
        self.postulacion.estado = Application.Estado.ACEPTADA
        self.postulacion.save()
        ApprovedProject.objects.filter(postulacion=self.postulacion).update(es_visible=True, titulo="Título publicado")
        self.postulacion.titulo = "Otro título"
        self.postulacion.save()
        self.assertEqual(ApprovedProject.objects.get().titulo, "Título publicado")

    def test_guardar_creada_no_crea_proyecto(self):
        self.postulacion.save()
        self.assertFalse(ApprovedProject.objects.exists())


class ConvocatoriaTests(BaseCompartida):
    def test_rechaza_fechas_que_se_cruzan(self):
        otra = Announcement(
            convenio=self.convocatoria.convenio,
            inicio=datetime.date(2026, 8, 1),
            cierre=datetime.date(2026, 9, 30),
            semestre="SP",
            anio=2026,
        )
        with self.assertRaisesMessage(ValidationError, "Ya existe un periodo"):
            otra.clean()

    def test_rechaza_cierre_antes_del_inicio(self):
        otra = Announcement(
            convenio=self.convocatoria.convenio,
            inicio=datetime.date(2027, 3, 1),
            cierre=datetime.date(2027, 2, 1),
            semestre="FA",
            anio=2027,
        )
        with self.assertRaisesMessage(ValidationError, "fecha de inicio"):
            otra.clean()

    def test_editar_la_misma_no_choca_consigo(self):
        self.convocatoria.clean()

    def test_enlace_a_sus_postulaciones(self):
        respuesta = self.client.get(reverse("admin:applications_announcement_changelist"))
        self.assertContains(respuesta, f"?convocatoria__id__exact={self.convocatoria.pk}")


class CorreoTests(BaseCompartida):
    def url(self, tipo):
        return reverse(f"admin:applications_application_{tipo}_correo", args=[self.postulacion.pk])

    def test_notificar_aceptada_trae_el_texto_de_aceptacion(self):
        Application.objects.filter(pk=self.postulacion.pk).update(estado=Application.Estado.ACEPTADA)
        respuesta = self.client.get(self.url("notificar"))
        self.assertContains(respuesta, "ha sido aceptado")
        self.assertContains(respuesta, "ana@ejemplo.cl")

    def test_notificar_creada_parte_con_saludo_y_firma(self):
        respuesta = self.client.get(self.url("notificar"))
        self.assertNotContains(respuesta, "ha sido")
        self.assertContains(respuesta, "Estimado/a")
        self.assertContains(respuesta, "Cecilia Bastarrica")
        self.assertContains(respuesta, "no está aceptada ni rechazada")

    def test_contactar_trae_saludo_y_firma_en_cualquier_estado(self):
        for estado in Application.Estado.values:
            Application.objects.filter(pk=self.postulacion.pk).update(estado=estado)
            with self.subTest(estado=estado):
                respuesta = self.client.get(self.url("contactar"))
                self.assertContains(respuesta, "Estimado/a")
                self.assertContains(respuesta, "Cecilia Bastarrica")
                self.assertNotContains(respuesta, "no está aceptada ni rechazada")

    def test_el_editor_muestra_el_membrete_y_el_pie_del_correo(self):
        respuesta = self.client.get(self.url("contactar"))
        self.assertContains(respuesta, f'<img src="{correo.LOGO}"')
        self.assertContains(respuesta, "Edificio Norte, Beauchef 851")
        self.client.post(self.url("contactar"), {"correo": "ana@ejemplo.cl", "asunto": "Reunión", "contenido": "<p>Hola</p>"})
        html = mail.outbox[0].alternatives[0].content
        self.assertIn(f'<img src="{correo.LOGO}"', html)
        self.assertIn("Edificio Norte, Beauchef 851", html)

    def test_enviar_marca_notificada(self):
        respuesta = self.client.post(
            self.url("contactar"), {"correo": "ana@ejemplo.cl", "asunto": "Reunión", "contenido": "<p>Hola</p>"}, follow=True
        )
        self.assertContains(respuesta, "Correo enviado exitosamente.")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@ejemplo.cl"])
        self.assertIn("<p>Hola</p>", mail.outbox[0].alternatives[0].content)
        self.postulacion.refresh_from_db()
        self.assertTrue(self.postulacion.fue_notificada)

    def test_el_texto_plano_conserva_los_parrafos(self):
        self.client.post(
            self.url("contactar"),
            {
                "correo": "ana@ejemplo.cl",
                "asunto": "Reunión",
                "contenido": "<p>Hola <strong>Ana</strong>:</p><p>Saludos,<br>Cecilia&nbsp;B.</p>",
            },
        )
        self.assertEqual(mail.outbox[0].body, "Hola Ana:\n\nSaludos,\nCecilia B.")

    def test_si_el_correo_falla_no_marca_notificada(self):
        with mock.patch("postulaciones.correo.EmailMultiAlternatives.send", side_effect=OSError("red caída")):
            respuesta = self.client.post(
                self.url("notificar"), {"correo": "ana@ejemplo.cl", "asunto": "Resultado", "contenido": "<p>x</p>"}
            )
        self.assertContains(respuesta, "No se pudo enviar el correo")
        self.postulacion.refresh_from_db()
        self.assertFalse(self.postulacion.fue_notificada)

    def test_sin_mensaje_no_envia(self):
        respuesta = self.client.post(self.url("notificar"), {"correo": "ana@ejemplo.cl", "asunto": "Resultado", "contenido": ""})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_requiere_permiso_de_cambio(self):
        lector = User.objects.create_user("lector", password="clave-de-prueba", is_staff=True)
        lector.user_permissions.add(Permission.objects.get(codename="view_application"))
        self.client.force_login(lector)
        self.assertEqual(self.client.get(self.url("notificar")).status_code, 403)

    def test_la_accion_de_fila_lleva_al_formulario(self):
        respuesta = self.client.get(reverse("admin:applications_application_notificar", args=[self.postulacion.pk]))
        self.assertRedirects(respuesta, self.url("notificar"))


class NavegacionTests(BaseCompartida):
    def test_las_siluetas_van_versionadas_y_en_cache(self):
        inicio = self.client.get(reverse("admin:index")).content.decode()
        url = inicio.split('const urlSiluetas = "', 1)[1].split('"', 1)[0]
        self.assertIn("?v=", url)
        respuesta = self.client.get(url)
        self.assertIn("immutable", respuesta["Cache-Control"])
        for forma in ["inicio", "listado", "ficha"]:
            self.assertContains(respuesta, f'data-forma="{forma}"')

    def test_el_documento_no_espera_a_alpine_para_mostrarse(self):
        for url in [reverse("admin:index"), reverse("admin:applications_application_changelist")]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'raiz.removeAttribute("x-cloak")')
        self.client.logout()
        self.assertContains(self.client.get(reverse("admin:login")), 'raiz.removeAttribute("x-cloak")')


class FormulariosTests(BaseCompartida):
    def test_cada_permiso_del_portal_aparece_una_vez(self):
        contenido = self.client.get(reverse("admin:auth_group_add")).content.decode()
        for modelo in ["application", "organization", "unit", "candidate", "approvedproject", "member", "announcement"]:
            for accion in ["view", "add", "change", "delete"]:
                pk = Permission.objects.get(codename=f"{accion}_{modelo}").pk
                with self.subTest(permiso=f"{accion}_{modelo}"):
                    self.assertEqual(contenido.count(f'name="permissions" value="{pk}"'), 1)

    def test_los_permisos_van_por_seccion_del_menu(self):
        respuesta = self.client.get(reverse("admin:auth_group_add"))
        self.assertContains(respuesta, '<caption id="id_permissions_seccion_1">Postulaciones</caption>', html=True)
        self.assertContains(respuesta, "Ver organizaciones")
        self.assertNotContains(respuesta, "permisos Disponibles")

    def test_guardar_conserva_un_permiso_ajeno(self):
        ajeno = Permission.objects.get(codename="view_session")
        propio = Permission.objects.get(codename="view_application")
        respuesta = self.client.post(reverse("admin:auth_group_add"), {"name": "Docentes", "permissions": [ajeno.pk, propio.pk]})
        self.assertEqual(respuesta.status_code, 302)
        grupo = Group.objects.get(name="Docentes")
        self.assertEqual(set(grupo.permissions.all()), {ajeno, propio})
        ficha = self.client.get(reverse("admin:auth_group_change", args=[grupo.pk]))
        self.assertContains(ficha, f'<input type="hidden" name="permissions" value="{ajeno.pk}">')
        self.assertContains(ficha, "Tiene 1 permiso que este portal no usa; se conserva al guardar.")

    def test_el_usuario_elige_grupos_con_casillas(self):
        Group.objects.create(name="Docentes")
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[self.docente.pk]))
        self.assertContains(respuesta, 'type="checkbox" name="groups"')
        self.assertNotContains(respuesta, "SelectFilter")

    def test_la_ficha_del_usuario_no_crea_grupos(self):
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[self.docente.pk]))
        self.assertNotContains(respuesta, 'id="add_id_groups"')
        self.assertNotContains(respuesta, 'aria-controls="related-widget-wrapper-groups"')

    def test_la_ficha_del_usuario_lleva_a_su_contrasena_sin_mostrar_el_hash(self):
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[self.docente.pk]))
        self.assertContains(respuesta, f'href="{reverse("admin:auth_user_password_change", args=[self.docente.pk])}"')
        self.assertContains(respuesta, "Cambiar la contraseña")
        self.assertNotContains(respuesta, "../password/")
        for dato in ["algoritmo", "iteraciones", "función resumen"]:
            with self.subTest(dato=dato):
                self.assertNotContains(respuesta, dato)

    def test_a_un_usuario_sin_contrasena_se_le_puede_asignar(self):
        externo = User.objects.create_user("externo")
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[externo.pk]))
        self.assertContains(respuesta, "Sin contraseña")
        self.assertContains(respuesta, f'href="{reverse("admin:auth_user_password_change", args=[externo.pk])}"')

    def test_quitar_un_integrante_es_una_casilla_con_nombre(self):
        proyecto = ApprovedProject.objects.create(titulo="Riego", semestre="SP", anio=2026, tutor="Tutor")
        Member.objects.create(proyecto=proyecto, nombre="Luis Soto")
        respuesta = self.client.get(reverse("admin:applications_approvedproject_change", args=[proyecto.pk]))
        self.assertContains(respuesta, 'class="delete sr-only" aria-label="Quitar Luis Soto"')
        self.assertContains(respuesta, '<button type="button" class="delete-template')
        self.assertContains(respuesta, "Quitar esta fila")

    def test_el_archivo_declara_sus_formatos(self):
        respuesta = self.client.get(reverse("admin:applications_application_add"))
        self.assertContains(respuesta, 'accept=".pdf"')
        self.assertContains(respuesta, "Formato PDF")
        self.assertContains(respuesta, "zona-archivo-destino")

    def test_el_filtro_por_convocatoria_no_carga_select2(self):
        Announcement.objects.create(
            convenio=self.convocatoria.convenio,
            inicio=datetime.date(2027, 3, 1),
            cierre=datetime.date(2027, 4, 30),
            semestre="FA",
            anio=2027,
        )
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, 'name="convocatoria__id__exact"')
        self.assertNotContains(respuesta, "select2")


class RestablecerTests(TestCase):
    def test_el_login_ofrece_restablecer(self):
        respuesta = self.client.get(reverse("admin:login"))
        self.assertContains(respuesta, reverse("admin_password_reset"))

    def test_el_formulario_responde(self):
        self.assertEqual(self.client.get(reverse("admin_password_reset")).status_code, 200)

    def test_los_campos_llevan_el_estilo_de_unfold(self):
        usuario = User.objects.create_user("ana", "ana@dcc.uchile.cl", "clave-de-prueba")
        for formulario in [RestablecerForm(), NuevaClaveForm(usuario)]:
            for campo in formulario:
                with self.subTest(campo=campo.name):
                    self.assertIn("border-base-200", campo.field.widget.attrs["class"])


class TextosTests(BaseCompartida):
    def test_las_altas_dicen_agregar(self):
        respuesta = self.client.get(reverse("admin:applications_unit_add"))
        self.assertContains(respuesta, "Agregar unidad")
        self.assertNotContains(respuesta, "Añadir")

    def test_las_fichas_dicen_editar(self):
        respuesta = self.client.get(reverse("admin:applications_application_change", args=[self.postulacion.pk]))
        self.assertContains(respuesta, "Editar postulación")
        self.assertNotContains(respuesta, "Modificar")

    def test_la_fila_en_linea_dice_que_agrega(self):
        proyecto = ApprovedProject.objects.create(titulo="Riego", semestre="SP", anio=2026, tutor="Tutor")
        respuesta = self.client.get(reverse("admin:applications_approvedproject_change", args=[proyecto.pk]))
        self.assertContains(respuesta, "<span>Agregar integrante</span>", html=True)
        self.assertNotContains(respuesta, "Integrante adicional.</span>")

    def test_borrar_en_bloque_no_concuerda_genero_ni_numero(self):
        borrable = Organization.objects.create(rut="1-9", nombre="Borrable")
        lista = reverse("admin:applications_organization_changelist")
        datos = {"action": "delete_selected", "index": "0", "_selected_action": [borrable.pk]}
        self.assertContains(self.client.post(lista, datos), "¿Seguro que quieres eliminar la selección?")
        respuesta = self.client.post(lista, {**datos, "post": "yes"}, follow=True)
        self.assertContains(respuesta, "Se eliminó la selección: 1 organización.")
        self.assertNotContains(respuesta, "seleccionado/s")


class HistorialTests(BaseCompartida):
    def registros(self):
        return LogEntry.objects.filter(object_id=str(self.postulacion.pk)).values_list("change_message", flat=True)

    def test_aceptar_y_rechazar_quedan_en_el_historial(self):
        for accion, mensaje, verbo in [("aceptar", "Aceptada.", "la aceptó"), ("rechazar", "Rechazada.", "la rechazó")]:
            with self.subTest(accion=accion):
                self.client.post(
                    reverse("admin:applications_application_changelist"),
                    {"action": accion, "index": "0", "_selected_action": [self.postulacion.pk]},
                )
                self.assertEqual(self.registros().first(), mensaje)
                ficha = self.client.get(reverse("admin:applications_application_change", args=[self.postulacion.pk]))
                self.assertContains(ficha, f"docente {verbo}")

    def test_los_correos_enviados_quedan_en_el_historial(self):
        for tipo, mensaje in [("notificar", "Notificada por correo: «Resultado»."), ("contactar", "Contactada por correo: «Resultado».")]:
            with self.subTest(tipo=tipo):
                self.client.post(
                    reverse(f"admin:applications_application_{tipo}_correo", args=[self.postulacion.pk]),
                    {"correo": "ana@ejemplo.cl", "asunto": "Resultado", "contenido": "<p>Hola</p>"},
                )
                self.assertEqual(self.registros().first(), mensaje)
        self.assertContains(self.client.get(reverse("admin:index")), "escribió al postulante de")

    def test_un_correo_que_no_sale_no_queda_en_el_historial(self):
        with mock.patch("postulaciones.correo.EmailMultiAlternatives.send", side_effect=OSError("red caída")):
            self.client.post(
                reverse("admin:applications_application_notificar_correo", args=[self.postulacion.pk]),
                {"correo": "ana@ejemplo.cl", "asunto": "Resultado", "contenido": "<p>x</p>"},
            )
        self.assertFalse(self.registros().exists())


class SinPagosTests(BaseCompartida):
    def test_no_hay_nada_del_portal_de_pagos(self):
        from django.conf import settings

        self.assertFalse(hasattr(settings, "URL_PORTAL_PAGOS"))
        for url in [reverse("admin:index"), reverse("admin:applications_application_changelist")]:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "pagos")


class PermisosAjenosTests(BaseCompartida):
    def test_la_ficha_no_lista_permisos_de_otros_sistemas(self):
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[self.docente.pk]))
        self.assertNotContains(respuesta, "Otros permisos")
        self.assertNotContains(respuesta, "Sesiones")
        self.assertNotContains(respuesta, "que este portal no usa")

    def test_guardar_un_usuario_conserva_sus_permisos_ajenos(self):
        ajeno = Permission.objects.get(codename="view_logentry")
        propio = Permission.objects.get(codename="view_application")
        externo = User.objects.create_user("externo", is_staff=True)
        externo.user_permissions.add(ajeno)
        ficha = self.client.get(reverse("admin:auth_user_change", args=[externo.pk])).content.decode()
        self.assertIn(f'<input type="hidden" name="user_permissions" value="{ajeno.pk}">', ficha)
        datos = {
            "username": "externo",
            "is_active": "on",
            "is_staff": "on",
            "user_permissions": [ajeno.pk, propio.pk],
            "date_joined_0": "01/10/2026",
            "date_joined_1": "10:00:00",
        }
        self.assertEqual(self.client.post(reverse("admin:auth_user_change", args=[externo.pk]), datos).status_code, 302)
        self.assertEqual(set(externo.user_permissions.all()), {ajeno, propio})


class BarraDeAccionesTests(BaseCompartida):
    def test_la_barra_va_despues_de_la_tabla(self):
        contenido = self.client.get(reverse("admin:applications_organization_changelist")).content.decode()
        self.assertLess(contenido.index('id="result_list"'), contenido.index('class="barra-acciones"'))

    def test_cada_accion_es_un_boton(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, 'data-accion="aceptar"')
        self.assertContains(respuesta, 'data-accion="rechazar"')
        self.assertContains(respuesta, "Quitar la selección")
        self.assertNotContains(respuesta, '<select name="action"')

    def test_cada_fila_se_edita_y_se_elimina_desde_su_menu(self):
        organizacion = Organization.objects.create(rut="1-9", nombre="Con menú")
        for accion, destino in [("editar_fila", "change"), ("eliminar_fila", "delete")]:
            with self.subTest(accion=accion):
                respuesta = self.client.get(reverse(f"admin:applications_organization_{accion}", args=[organizacion.pk]))
                self.assertRedirects(respuesta, reverse(f"admin:applications_organization_{destino}", args=[organizacion.pk]))

    def test_sin_permiso_de_borrar_no_hay_eliminar_por_fila(self):
        lector = User.objects.create_user("lector", password="clave-de-prueba", is_staff=True)
        lector.user_permissions.add(Permission.objects.get(codename="view_application"))
        self.client.force_login(lector)
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertNotContains(respuesta, "eliminar-fila")


class EmergentesTests(BaseCompartida):
    def test_las_emergentes_no_se_inscriben_en_la_transicion_entre_vistas(self):
        alta = reverse("admin:applications_organization_add")
        self.assertContains(self.client.get(alta), "@view-transition")
        self.assertNotContains(self.client.get(alta, {"_popup": "1", "_to_field": "id"}), "@view-transition")


class BorradoEnBloqueTests(BaseCompartida):
    def setUp(self):
        super().setUp()
        self.otra = Application.objects.create(
            postulante=self.postulacion.postulante,
            convocatoria=self.convocatoria,
            unidad=self.postulacion.unidad,
            titulo="Sistema de compras",
            archivo=SimpleUploadedFile("perfil.pdf", b"%PDF-1.4"),
        )

    def borrar(self, postulaciones, **extra):
        datos = {"action": "delete_selected", "index": "0", "_selected_action": [p.pk for p in postulaciones], **extra}
        return self.client.post(reverse("admin:applications_application_changelist"), datos, follow=True)

    def test_borrar_varias_espera_antes_de_confirmar(self):
        respuesta = self.borrar([self.postulacion, self.otra])
        self.assertContains(respuesta, "Eliminar la selección")
        self.assertContains(respuesta, 'disabled data-espera="5"')
        self.assertContains(respuesta, "Podrás confirmar en 5 segundos.")
        self.assertEqual(Application.objects.filter(pk__in=[self.postulacion.pk, self.otra.pk]).count(), 2)

    def test_borrar_una_marcada_no_espera(self):
        respuesta = self.borrar([self.postulacion])
        self.assertContains(respuesta, "Eliminar la selección")
        self.assertNotContains(respuesta, "data-espera")

    def test_confirmar_borra_las_postulaciones(self):
        self.assertContains(self.borrar([self.postulacion, self.otra], post="yes"), "Se eliminó la selección: 2 postulaciones.")
        self.assertFalse(Application.objects.filter(pk__in=[self.postulacion.pk, self.otra.pk]).exists())

    def test_borrar_una_no_espera(self):
        respuesta = self.client.get(reverse("admin:applications_application_delete", args=[self.postulacion.pk]))
        self.assertNotContains(respuesta, "data-espera")


class AccionesPorFilaTests(BaseCompartida):
    def url(self, accion):
        return reverse(f"admin:applications_application_{accion}_fila", args=[self.postulacion.pk])

    def test_el_menu_acepta_y_rechaza_por_post(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        for accion in ["aceptar", "rechazar"]:
            with self.subTest(accion=accion):
                self.assertContains(respuesta, f'form="changelist-form" formaction="{self.url(accion)}" formmethod="post"')

    def test_aceptar_desde_la_fila_vuelve_al_listado(self):
        lista = reverse("admin:applications_application_changelist") + "?estado__exact=CR"
        respuesta = self.client.post(self.url("aceptar"), HTTP_REFERER="http://testserver" + lista)
        self.assertRedirects(respuesta, "http://testserver" + lista, fetch_redirect_response=False)
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.ACEPTADA)
        self.assertEqual(LogEntry.objects.get(object_id=str(self.postulacion.pk)).change_message, "Aceptada.")

    def test_un_get_no_cambia_nada(self):
        self.assertEqual(self.client.get(self.url("rechazar")).status_code, 405)
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.CREADA)

    def test_sin_permiso_de_edicion_no_acepta(self):
        lector = User.objects.create_user("lector", password="clave-de-prueba", is_staff=True)
        lector.user_permissions.add(Permission.objects.get(codename="view_application"))
        self.client.force_login(lector)
        self.assertEqual(self.client.post(self.url("aceptar")).status_code, 403)
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.CREADA)


class PaginacionTests(BaseCompartida):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Organization.objects.bulk_create(Organization(rut=f"{n}-K", nombre=f"Organización {n:02}") for n in range(25))

    def test_lleva_a_la_primera_la_anterior_la_siguiente_y_la_ultima(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"), {"p": 2})
        self.assertContains(respuesta, '<a href="?p=1" class="boton-secundario px-3" aria-label="Primera página">')
        self.assertContains(respuesta, '<a href="?p=1" class="boton-secundario max-sm:px-3" rel="prev">')
        self.assertContains(respuesta, '<a href="?p=3" class="boton-secundario max-sm:px-3" rel="next">')
        self.assertContains(respuesta, '<a href="?p=3" class="boton-secundario px-3" aria-label="Última página">')
        self.assertContains(respuesta, '<span class="whitespace-nowrap">11 a 20</span> de 26 organizaciones')

    def test_en_los_extremos_los_botones_quedan_inactivos(self):
        url = reverse("admin:applications_organization_changelist")
        primera = self.client.get(url)
        self.assertContains(primera, 'disabled aria-label="Primera página"')
        self.assertNotContains(primera, 'aria-label="Última página" disabled')
        ultima = self.client.get(url, {"p": 3})
        self.assertContains(ultima, 'disabled aria-label="Última página"')
        self.assertContains(ultima, '<span class="whitespace-nowrap">21 a 26</span> de 26 organizaciones')

    def test_conserva_el_orden_y_la_busqueda_al_cambiar_de_pagina(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"), {"o": "2", "q": "Organización"})
        self.assertContains(respuesta, 'href="?o=2&amp;p=2&amp;q=Organizaci%C3%B3n"')

    def test_la_cantidad_de_numeros_no_cambia_con_la_pagina(self):
        for total in [8, 39, 100]:
            for actual in range(1, total + 1):
                with self.subTest(total=total, actual=actual):
                    cl = SimpleNamespace(page_num=actual, paginator=SimpleNamespace(num_pages=total, ELLIPSIS="…"))
                    paginas = paginas_cercanas(cl)
                    self.assertEqual(len(paginas), 7)
                    self.assertTrue({1, actual, total} <= set(paginas))
        cl = SimpleNamespace(page_num=4, paginator=SimpleNamespace(num_pages=39, ELLIPSIS="…"))
        self.assertEqual(paginas_cercanas(cl), [1, 2, 3, 4, 5, "…", 39])

    def test_una_sola_pagina_muestra_solo_el_conteo(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, "1 postulación")
        self.assertNotContains(respuesta, 'aria-label="Paginación"')


class OrdenTests(BaseCompartida):
    def test_cada_encabezado_ordena_por_una_sola_columna(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"), {"o": "2"})
        self.assertContains(respuesta, 'aria-sort="ascending"', count=1)
        self.assertContains(respuesta, '<a href="?o=-2" id="orden-3" class="encabezado-orden" data-orden="ascendente" aria-describedby="orden-descendente">')
        self.assertContains(respuesta, '<a href="?o=1" id="orden-2" class="encabezado-orden" aria-describedby="orden-ascendente">')
        self.assertContains(respuesta, '<span id="orden-descendente" hidden>Ordenar de forma descendente</span>')

    def test_las_columnas_calculadas_no_se_ofrecen_para_ordenar(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, "<span>Título</span>")
        self.assertNotContains(respuesta, "<span>Organización</span>")


class ListadoParcialTests(BaseCompartida):
    def pedir(self, zona, url=None, **parametros):
        return self.client.get(url or reverse("admin:applications_application_changelist"), parametros, HTTP_HX_REQUEST="true", HTTP_HX_TARGET=zona)

    def test_htmx_recibe_solo_la_zona_del_listado(self):
        respuesta = self.pedir("listado")
        self.assertTemplateUsed(respuesta, "admin/listado_parcial.html")
        self.assertNotContains(respuesta, "<html")
        self.assertContains(respuesta, 'aria-label="Filtrar por estado"')
        self.assertContains(respuesta, '<div id="pie-listado" hx-swap-oob="innerHTML">')
        self.assertContains(respuesta, '<span id="conteo-cabecera" hx-swap-oob="innerHTML">')
        self.assertContains(respuesta, '<div id="contenido-filtros" hx-swap-oob="innerHTML">')

    def test_al_paginar_recibe_solo_la_tabla_y_el_pie(self):
        with mock.patch.object(admin.site._registry[Application].__class__, "filtros_estado") as filtros:
            respuesta = self.pedir("resultados-listado")
        filtros.assert_not_called()
        self.assertTemplateUsed(respuesta, "admin/listado_resultados.html")
        self.assertContains(respuesta, "Sistema de riego")
        self.assertContains(respuesta, '<div id="pie-listado" hx-swap-oob="innerHTML">')
        self.assertNotContains(respuesta, 'aria-label="Filtrar por estado"')
        self.assertNotContains(respuesta, 'id="contenido-filtros"')

    def test_sin_htmx_responde_la_pagina_completa(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, "<html")
        self.assertIn("HX-Request", respuesta["Vary"])
        self.assertIn("HX-Target", respuesta["Vary"])

    def test_otra_zona_de_htmx_recibe_la_pagina_completa(self):
        self.assertContains(self.pedir("modal-content"), "<html")

    def test_la_confirmacion_de_borrado_no_se_vuelve_fragmento(self):
        respuesta = self.client.post(
            reverse("admin:applications_application_changelist"),
            {"action": "delete_selected", "_selected_action": [self.postulacion.pk], "index": 0},
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="listado",
        )
        self.assertTemplateNotUsed(respuesta, "admin/listado_parcial.html")
        self.assertContains(respuesta, "<html")

    def test_el_listado_no_carga_actions_js(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertNotContains(respuesta, "admin/js/actions.js")
        self.assertContains(respuesta, "admin/js/core.js")

    def test_los_filtros_conservan_la_busqueda_pero_no_la_pagina(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"), {"q": "riego", "p": "1"})
        self.assertContains(respuesta, '<input type="hidden" name="q" value="riego">')
        self.assertNotContains(respuesta, '<input type="hidden" name="p"')

    def test_todos_los_listados_responden_fragmentos(self):
        for modelo in admin.site._registry:
            url = reverse(f"admin:{modelo._meta.app_label}_{modelo._meta.model_name}_changelist")
            for zona, plantilla in [("listado", "admin/listado_parcial.html"), ("resultados-listado", "admin/listado_resultados.html")]:
                with self.subTest(url=url, zona=zona):
                    self.assertTemplateUsed(self.pedir(zona, url), plantilla)


class MenusDeFilaTests(BaseCompartida):
    def test_los_menus_no_quedan_atados_mientras_estan_cerrados(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, 'x-data="menuEmergente"')
        self.assertNotContains(respuesta, "x-anchor")


class ColumnasFijasTests(BaseCompartida):
    def test_la_columna_de_acciones_tiene_encabezado(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, '<th scope="col" class="columna-acciones w-px"><span class="sr-only">Acciones</span></th>')


class TextosDeDjangoTests(BaseCompartida):
    def test_la_extension_no_permitida_se_escribe_con_tilde(self):
        logo = SimpleUploadedFile("logo.txt", b"texto")
        respuesta = self.client.post(reverse("admin:applications_unit_add"), {"nombre": "Unidad", "logo": logo, "_save": "1"})
        self.assertContains(respuesta, "no está permitida")

    def test_los_errores_de_django_tutean(self):
        organizacion = Organization.objects.first()
        respuesta = self.client.post(
            reverse("admin:applications_candidate_add"), {"organizacion": organizacion.pk, "correo": "no-es-correo", "_save": "1"}
        )
        self.assertContains(respuesta, "Escribe un correo válido")
        self.assertNotContains(respuesta, "Introduzca")

    def test_las_fechas_de_convocatoria_indican_el_formato(self):
        respuesta = self.client.get(reverse("admin:applications_announcement_add"))
        self.assertContains(respuesta, "Día/mes/año, por ejemplo 15/03/2027.", count=2)

    def test_la_ayuda_del_nombre_de_usuario_esta_bien_escrita(self):
        respuesta = self.client.get(reverse("admin:auth_user_add"))
        self.assertContains(respuesta, "Hasta 150 caracteres")
        self.assertNotContains(respuesta, "carácteres")


class UnidadesTests(BaseCompartida):
    def test_la_unidad_necesita_nombre(self):
        antes = Unit.objects.count()
        respuesta = self.client.post(reverse("admin:applications_unit_add"), {"nombre": "", "_save": "1"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Este campo es obligatorio.")
        self.assertEqual(Unit.objects.count(), antes)


class ArchivosTests(BaseCompartida):
    def test_el_error_del_archivo_queda_asociado_al_campo(self):
        respuesta = self.client.post(reverse("admin:commons_rulesapplications_add"), {"descripcion": "Formato", "_save": "1"})
        self.assertContains(respuesta, 'aria-describedby="id_perfil_de_proyecto_zona id_perfil_de_proyecto_error"')


class CuentaPropiaTests(BaseCompartida):
    def test_la_ficha_propia_no_deja_quitarse_el_acceso(self):
        url = reverse("admin:auth_user_change", args=[self.docente.pk])
        respuesta = self.client.get(url)
        self.assertContains(respuesta, "Tu propio acceso lo cambia otra persona que administre las cuentas.")
        self.client.post(
            url,
            {
                "username": "docente",
                "first_name": "Ana",
                "last_name": "",
                "email": "docente@dcc.uchile.cl",
                "is_active": "",
                "is_staff": "",
                "is_superuser": "",
                "date_joined_0": timezone.localtime(self.docente.date_joined).strftime("%d/%m/%Y"),
                "date_joined_1": timezone.localtime(self.docente.date_joined).strftime("%H:%M:%S"),
                "_save": "1",
            },
        )
        self.docente.refresh_from_db()
        self.assertEqual(self.docente.first_name, "Ana")
        self.assertTrue(self.docente.is_active and self.docente.is_staff and self.docente.is_superuser)

    def test_la_cuenta_propia_no_se_elimina(self):
        respuesta = self.client.get(reverse("admin:auth_user_delete", args=[self.docente.pk]), follow=True)
        self.assertRedirects(respuesta, reverse("admin:auth_user_change", args=[self.docente.pk]))
        self.assertContains(respuesta, "Tu propia cuenta no se puede eliminar desde aquí.")
        self.assertTrue(User.objects.filter(pk=self.docente.pk).exists())

    def test_el_borrado_en_lote_con_la_cuenta_propia_se_detiene(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba")
        respuesta = self.client.post(
            reverse("admin:auth_user_changelist"), {"action": "delete_selected", "_selected_action": [self.docente.pk, otra.pk]}
        )
        self.assertContains(respuesta, "tu propia cuenta (quítala de la selección)")
        self.client.post(
            reverse("admin:auth_user_changelist"),
            {"action": "delete_selected", "_selected_action": [self.docente.pk, otra.pk], "post": "yes"},
        )
        self.assertEqual(User.objects.filter(pk__in=[self.docente.pk, otra.pk]).count(), 2)

    def test_el_menu_de_la_fila_propia_no_ofrece_eliminar(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba")
        respuesta = self.client.get(reverse("admin:auth_user_changelist")).content.decode()
        self.assertNotIn(reverse("admin:auth_user_eliminar_fila", args=[self.docente.pk]), respuesta)
        self.assertIn(reverse("admin:auth_user_eliminar_fila", args=[otra.pk]), respuesta)

    def test_otra_cuenta_conserva_el_acceso_editable(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba", is_staff=True)
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[otra.pk]))
        self.assertNotContains(respuesta, "Tu propio acceso lo cambia otra persona")


class IngresoTests(TestCase):
    def test_un_ingreso_fallido_muestra_un_solo_aviso_asociado_a_los_campos(self):
        User.objects.create_user("persona", password="clave-de-prueba", is_staff=True)
        respuesta = self.client.post(reverse("admin:login"), {"username": "persona", "password": "otra"})
        contenido = respuesta.content.decode()
        self.assertEqual(contenido.count("errornote"), 1)
        self.assertIn("No pudimos ingresar con ese nombre de usuario y esa contraseña.", contenido)
        self.assertEqual(contenido.count('aria-describedby="error-ingreso"'), 2)
        self.assertIn('id="error-ingreso"', contenido)

    def test_llegar_desde_otra_pagina_explica_que_hay_que_ingresar(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"), follow=True)
        self.assertContains(respuesta, "Para ver esa página, primero ingresa con tu cuenta.")
        self.assertNotContains(self.client.get(reverse("admin:login")), "Para ver esa página")


class InicioYMenuTests(BaseCompartida):
    def test_el_menu_omite_los_grupos_sin_secciones_permitidas(self):
        lector = User.objects.create_user("lector", password="clave-de-prueba", is_staff=True)
        lector.user_permissions.add(Permission.objects.get(codename="view_application"))
        self.client.force_login(lector)
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, 'class="lateral-grupo">Postulaciones</h2>')
        self.assertNotContains(respuesta, 'class="lateral-grupo">Proyectos</h2>')

    def test_un_personal_sin_permisos_ve_el_aviso(self):
        sin_permisos = User.objects.create_user("sin-permisos", password="clave-de-prueba", is_staff=True)
        self.client.force_login(sin_permisos)
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, "Tu cuenta todavía no tiene permisos en ninguna sección.")

    def test_la_actividad_solo_muestra_lo_que_la_cuenta_puede_ver(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba")
        LogEntry.objects.log_actions(user_id=self.docente.pk, queryset=[otra], action_flag=ADDITION)
        LogEntry.objects.log_actions(user_id=self.docente.pk, queryset=[self.postulacion], action_flag=ADDITION)
        lector = User.objects.create_user("lector", password="clave-de-prueba", is_staff=True)
        lector.user_permissions.add(Permission.objects.get(codename="view_application"))
        self.client.force_login(lector)
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, "Sistema de riego</a>")
        self.assertNotContains(respuesta, reverse("admin:auth_user_change", args=[otra.pk]))
        self.assertNotContains(respuesta, "Tu cuenta todavía no tiene permisos")


class ActividadSinNombreTests(BaseCompartida):
    def test_la_actividad_nombra_los_registros_sin_nombre(self):
        unidad = Unit.objects.create(nombre="")
        LogEntry.objects.log_actions(user_id=self.docente.pk, queryset=[unidad], action_flag=ADDITION)
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, "(sin nombre)</a>")


class CasillasDeFilaTests(BaseCompartida):
    def test_cada_casilla_nombra_su_fila(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertContains(respuesta, 'aria-label="Seleccionar «Sistema de riego»"')
        self.assertNotContains(respuesta, 'aria-label="Seleccionar el registro"')


class LoteTests(BaseCompartida):
    def test_aceptar_en_lote_no_toca_las_que_ya_estaban_aceptadas(self):
        otra = Application.objects.create(
            postulante=self.postulacion.postulante,
            convocatoria=self.convocatoria,
            unidad=self.postulacion.unidad,
            titulo="Inventario",
            archivo=SimpleUploadedFile("otro.pdf", b"%PDF-1.4"),
            estado=Application.Estado.ACEPTADA,
            fue_notificada=True,
        )
        respuesta = self.client.post(
            reverse("admin:applications_application_changelist"),
            {"action": "aceptar", "_selected_action": [self.postulacion.pk, otra.pk]},
            follow=True,
        )
        otra.refresh_from_db()
        self.assertTrue(otra.fue_notificada)
        self.assertContains(respuesta, "Se aceptó 1 postulación. 1 ya estaba aceptada y no cambió.")
        self.assertEqual(LogEntry.objects.filter(object_id=str(otra.pk)).count(), 0)

    def test_aceptar_solo_las_ya_aceptadas_no_cambia_nada(self):
        Application.objects.filter(pk=self.postulacion.pk).update(estado=Application.Estado.ACEPTADA, fue_notificada=True)
        respuesta = self.client.post(
            reverse("admin:applications_application_changelist"),
            {"action": "aceptar", "_selected_action": [self.postulacion.pk]},
            follow=True,
        )
        self.postulacion.refresh_from_db()
        self.assertTrue(self.postulacion.fue_notificada)
        self.assertContains(respuesta, "Las postulaciones elegidas ya estaban aceptadas; no cambió nada.")


class EmergentesAccesiblesTests(BaseCompartida):
    def test_la_capa_de_las_emergentes_es_un_dialogo(self):
        respuesta = self.client.get(reverse("admin:applications_unit_add"))
        self.assertContains(respuesta, '<div id="capa-emergente" role="dialog" aria-modal="true"')


class BuscadorTests(BaseCompartida):
    def test_el_buscador_es_un_combobox_con_lista(self):
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, 'role="combobox"')
        self.assertContains(respuesta, "aria-activedescendant")


class AyudasTests(BaseCompartida):
    def test_cada_ayuda_tiene_el_id_que_la_describe(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba", is_staff=True)
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[otra.pk]))
        self.assertContains(respuesta, 'aria-describedby="id_username_helptext"')
        self.assertContains(respuesta, 'id="id_username_helptext"')


class CamposDeFechaTests(BaseCompartida):
    def test_los_campos_de_fecha_y_hora_van_en_un_grupo_con_nombre(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba", is_staff=True)
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[otra.pk]))
        self.assertContains(respuesta, 'id="id_date_joined_etiqueta"')
        self.assertContains(respuesta, 'role="group" aria-labelledby="id_date_joined_etiqueta"')


class MatricesDeshabilitadasTests(BaseCompartida):
    def test_las_matrices_deshabilitadas_se_recorren_con_teclado(self):
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[self.docente.pk]))
        self.assertContains(respuesta, 'role="region" tabindex="0" aria-labelledby="id_user_permissions_seccion_1"')
        self.assertContains(respuesta, '<caption id="id_user_permissions_seccion_1">')


class CabeceraDeIntegrantesTests(BaseCompartida):
    def test_la_cabecera_de_integrantes_se_ve_en_todos_los_anchos(self):
        proyecto = ApprovedProject.objects.create(titulo="Riego", semestre="SP", anio=2026, tutor="Tutor")
        respuesta = self.client.get(reverse("admin:applications_approvedproject_change", args=[proyecto.pk]))
        self.assertContains(respuesta, '<thead class="relative">')
        self.assertNotContains(respuesta, "lg:table-header-group")
        self.assertContains(respuesta, '<span class="sr-only">Quitar</span>')


class BuscadorComoEnlaceTests(BaseCompartida):
    def test_el_enter_del_buscador_pasa_por_el_enlace(self):
        respuesta = self.client.get(reverse("admin:index"))
        self.assertContains(respuesta, "document.getElementById('resultado-busqueda-' + currentIndex)?.click()")

    def test_los_resultados_del_buscador_navegan_como_enlaces(self):
        respuesta = self.client.get(reverse("admin:search"), {"s": "Fundación"})
        self.assertContains(respuesta, 'id="resultado-busqueda-1"')
        self.assertNotContains(respuesta, "selectItem")


class TraduccionesDeDjangoTests(BaseCompartida):
    def test_los_selectores_de_fecha_y_la_ayuda_de_activa_estan_traducidos(self):
        respuesta = self.client.get(reverse("admin:jsi18n"))
        self.assertContains(respuesta, "Elegir la fecha")
        self.assertContains(respuesta, "Elegir la hora")
        otra = User.objects.create_user("otra", password="clave-de-prueba", is_staff=True)
        respuesta = self.client.get(reverse("admin:auth_user_change", args=[otra.pk]))
        self.assertContains(respuesta, "Indica si la cuenta puede ingresar.")

    def test_el_alta_de_cuenta_explica_el_ingreso_sin_contrasena(self):
        respuesta = self.client.get(reverse("admin:auth_user_add"))
        self.assertContains(respuesta, "Ingreso con contraseña")
        self.assertContains(respuesta, "no puede ingresar ni recuperar la contraseña")
        self.assertNotContains(respuesta, "Single Sign-On")
        self.assertContains(respuesta, "La contraseña no puede tener solo números.")
        self.assertNotContains(respuesta, "Tu contraseña")

    def test_el_historial_dice_que_cambio(self):
        otra = User.objects.create_user("otra", password="clave-de-prueba", is_staff=True)
        url = reverse("admin:auth_user_password_change", args=[otra.pk])
        self.client.post(url, {"password1": "otra-clave-larga-2026", "password2": "otra-clave-larga-2026", "usable_password": "true"})
        respuesta = self.client.get(reverse("admin:auth_user_history", args=[otra.pk]))
        self.assertContains(respuesta, "Cambios en contraseña.")
        self.assertNotContains(respuesta, "Modificado")

    def test_los_campos_de_acceso_tienen_nombres_claros(self):
        respuesta = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertContains(respuesta, "Acceso a la administración")
        self.assertNotContains(respuesta, "Es staff")
        self.assertNotContains(respuesta, "estado de superusuario")


class BusquedaSinTildesTests(BaseCompartida):
    def test_encuentra_sin_tildes_en_los_listados(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"), {"q": "fundacion"})
        self.assertContains(respuesta, "Fundación Ejemplo")
        respuesta = self.client.get(reverse("admin:applications_application_changelist"), {"q": "RIEGO fundacion"})
        self.assertContains(respuesta, "Sistema de riego")

    def test_cada_palabra_tiene_que_aparecer(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"), {"q": "riego inexistente"})
        self.assertNotContains(respuesta, "Sistema de riego")

    def test_los_campos_que_no_son_texto_se_buscan_como_antes(self):
        respuesta = self.client.get(reverse("admin:applications_announcement_changelist"), {"q": "2026"})
        self.assertContains(respuesta, f'{reverse("admin:applications_announcement_change", args=[self.convocatoria.pk])}?_changelist_filters=q%3D2026')

    def test_el_buscador_de_la_cabecera_tampoco_distingue_tildes(self):
        respuesta = self.client.get(reverse("admin:search"), {"s": "fundacion"})
        self.assertContains(respuesta, "Fundación Ejemplo")
