import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase

from core.functions import get_env_variable


class RutasAntiguasTests(TestCase):
    def test_lleva_a_la_ruta_nueva(self):
        respuesta = self.client.get("/admin/applications/application/482/change/")
        self.assertEqual(respuesta.status_code, 301)
        self.assertEqual(respuesta["Location"], "/postulaciones/482/")

    def test_conserva_la_consulta(self):
        respuesta = self.client.get("/admin/applications/application/?q=feria")
        self.assertEqual(respuesta["Location"], "/postulaciones/?q=feria")

    def test_no_sale_del_sitio(self):
        for ruta in ["/admin//evil.example/", "/admin/\\evil.example/", "/admin//\\evil.example/"]:
            with self.subTest(ruta=ruta):
                destino = self.client.get(ruta)["Location"]
                self.assertTrue(destino.startswith("/"))
                self.assertFalse(destino.startswith(("//", "/\\")))


class VariablesDeEntornoTests(SimpleTestCase):
    def test_obligatoria_vacia_no_pasa(self):
        with mock.patch.dict(os.environ, {"PRUEBA_OBLIGATORIA": ""}), self.assertRaises(ImproperlyConfigured):
            get_env_variable("PRUEBA_OBLIGATORIA")

    def test_opcional_vacia_toma_el_valor_por_omision(self):
        with mock.patch.dict(os.environ, {"PRUEBA_OPCIONAL": ""}):
            self.assertEqual(get_env_variable("PRUEBA_OPCIONAL", "por omisión"), "por omisión")
