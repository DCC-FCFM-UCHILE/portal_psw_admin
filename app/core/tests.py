from django.test import TestCase


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
