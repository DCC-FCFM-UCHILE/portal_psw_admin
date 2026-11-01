import datetime
from unittest import mock

from django.contrib.auth.models import Group, Permission, User
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from convenios.models import RulesApplications
from cuentas.forms import NuevaClaveForm, RestablecerForm
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

    def test_no_ofrece_borrar_en_bloque(self):
        respuesta = self.client.get(reverse("admin:applications_application_changelist"))
        self.assertNotContains(respuesta, 'value="delete_selected"')

    def test_los_buscadores_no_muestran_atajos_de_teclado(self):
        for url in [reverse("admin:index"), reverse("admin:applications_application_changelist")]:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "<kbd")

    def test_el_buscador_del_listado_ocupa_el_ancho_disponible(self):
        respuesta = self.client.get(reverse("admin:applications_organization_changelist"))
        self.assertContains(respuesta, '<div id="toolbar" class="sm:grow lg:grow-0">')


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
        self.assertContains(respuesta, "Postulaciones actualizadas a aceptadas.")

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
    def test_cada_permiso_aparece_una_vez(self):
        respuesta = self.client.get(reverse("admin:auth_group_add"))
        valores = [f'value="{pk}"' for pk in Permission.objects.values_list("pk", flat=True)]
        contenido = respuesta.content.decode()
        self.assertEqual(contenido.count('name="permissions"'), len(valores))
        for valor in valores:
            with self.subTest(valor=valor):
                self.assertEqual(contenido.count(valor), 1)

    def test_los_permisos_van_por_seccion_del_menu(self):
        respuesta = self.client.get(reverse("admin:auth_group_add"))
        self.assertContains(respuesta, "<caption>Postulaciones</caption>", html=True)
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
        self.assertContains(ficha, "data-otros open")

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
