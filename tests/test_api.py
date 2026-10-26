"""Pruebas de los endpoints REST y de las páginas, con el cliente de prueba de Flask."""

import unittest

from app import create_app
from tests.utilidades import servicio_temporal


class ApiTest(unittest.TestCase):
    def setUp(self):
        servicio, _ = servicio_temporal(self)
        app = create_app(servicio)
        app.config["TESTING"] = True
        self.cliente = app.test_client()

    def test_catalogo_responde_con_formato_comun(self):
        respuesta = self.cliente.get("/api/pokemon")
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.get_json()
        self.assertTrue(cuerpo["ok"])
        self.assertEqual(len(cuerpo["datos"]), 15)

    def test_filtro_por_tipo(self):
        datos = self.cliente.get("/api/pokemon?tipo=Fuego").get_json()["datos"]
        self.assertEqual(len(datos), 4)

    def test_tipo_invalido_devuelve_400(self):
        respuesta = self.cliente.get("/api/pokemon?tipo=Mágico")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.get_json()["error"]["codigo"], "validacion")

    def test_pokemon_inexistente_devuelve_404(self):
        respuesta = self.cliente.get("/api/pokemon/999")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.get_json()["error"]["codigo"], "no_encontrado")

    def test_id_no_numerico_devuelve_error_json(self):
        respuesta = self.cliente.get("/api/pokemon/abc")
        self.assertEqual(respuesta.status_code, 404)
        self.assertFalse(respuesta.get_json()["ok"])

    def test_metodo_no_permitido_devuelve_json(self):
        respuesta = self.cliente.delete("/api/pokemon")
        self.assertEqual(respuesta.status_code, 405)
        self.assertFalse(respuesta.get_json()["ok"])

    def test_evoluciones_de_eevee(self):
        datos = self.cliente.get("/api/pokemon/133/evoluciones").get_json()["datos"]
        self.assertTrue(datos["tiene_evoluciones"])
        self.assertEqual(len(datos["arbol"]["hijos"]), 5)

    def test_registrar_pokemon_devuelve_201(self):
        respuesta = self.cliente.post(
            "/api/pokemon", json={"id": 25, "nombre": "Pikachu", "tipos": ["Eléctrico"]}
        )
        self.assertEqual(respuesta.status_code, 201)

    def test_registrar_duplicado_devuelve_409(self):
        respuesta = self.cliente.post(
            "/api/pokemon", json={"id": 1, "nombre": "Otro", "tipos": ["Normal"]}
        )
        self.assertEqual(respuesta.status_code, 409)

    def test_cuerpo_que_no_es_json_devuelve_400(self):
        respuesta = self.cliente.post("/api/pokemon", data="texto plano", content_type="text/plain")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.get_json()["error"]["codigo"], "validacion")

    def test_actualizar_pokemon(self):
        respuesta = self.cliente.put("/api/pokemon/1", json={"descripcion": "Nueva"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()["datos"]["descripcion"], "Nueva")

    def test_crear_evolucion_devuelve_201_y_conflictos_409(self):
        self.cliente.post("/api/pokemon", json={"id": 172, "nombre": "Pichu", "tipos": ["Eléctrico"]})
        self.cliente.post("/api/pokemon", json={"id": 25, "nombre": "Pikachu", "tipos": ["Eléctrico"]})
        ok = self.cliente.post("/api/evoluciones", json={"padre_id": 172, "hijo_id": 25})
        self.assertEqual(ok.status_code, 201)
        repetida = self.cliente.post("/api/evoluciones", json={"padre_id": 172, "hijo_id": 25})
        self.assertEqual(repetida.status_code, 409)

    def test_crear_evolucion_consigo_mismo(self):
        respuesta = self.cliente.post("/api/evoluciones", json={"padre_id": 1, "hijo_id": 1})
        self.assertEqual(respuesta.status_code, 409)

    def test_busqueda_con_algoritmos(self):
        for algoritmo in ("dfs", "bfs"):
            datos = self.cliente.get(f"/api/buscar?q=Umbreon&algoritmo={algoritmo}").get_json()["datos"]
            self.assertTrue(datos["encontrado"])
            self.assertEqual(datos["algoritmo"], algoritmo)

    def test_busqueda_sin_texto_devuelve_400(self):
        self.assertEqual(self.cliente.get("/api/buscar").status_code, 400)

    def test_busqueda_con_algoritmo_invalido_devuelve_400(self):
        self.assertEqual(self.cliente.get("/api/buscar?q=Eevee&algoritmo=xyz").status_code, 400)

    def test_recorrido_comparado(self):
        datos = self.cliente.get("/api/recorrido?algoritmo=comparar&raiz=Eevee").get_json()["datos"]
        self.assertIn("mismo_orden", datos)
        self.assertEqual(len(datos["dfs"]["orden"]), 6)

    def test_recorrido_con_algoritmo_invalido(self):
        self.assertEqual(self.cliente.get("/api/recorrido?algoritmo=zzz").status_code, 400)

    def test_tipos_y_estadisticas(self):
        tipos = self.cliente.get("/api/tipos").get_json()["datos"]
        self.assertIn("Fuego", tipos)
        estadisticas = self.cliente.get("/api/estadisticas").get_json()["datos"]
        self.assertEqual(estadisticas["total_pokemon"], 15)


class PaginasTest(unittest.TestCase):
    def setUp(self):
        servicio, _ = servicio_temporal(self)
        self.cliente = create_app(servicio).test_client()

    def test_inicio(self):
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("PokéDex Explorer", respuesta.get_data(as_text=True))

    def test_explorar_redirige_al_primer_pokemon(self):
        respuesta = self.cliente.get("/explorar")
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.location.endswith("/explorar/1"))

    def test_explorar_pokemon(self):
        self.assertEqual(self.cliente.get("/explorar/133").status_code, 200)

    def test_administracion(self):
        self.assertEqual(self.cliente.get("/admin").status_code, 200)


if __name__ == "__main__":
    unittest.main()
