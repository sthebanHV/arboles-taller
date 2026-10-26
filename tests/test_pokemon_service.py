"""Pruebas del servicio: reglas de negocio, persistencia y consultas sobre los datos de ejemplo."""

import json
import unittest

from models.errores import ErrorConflicto, ErrorNoEncontrado, ErrorValidacion
from repositories.pokemon_repository import PokemonRepository
from services.pokemon_service import PokemonService
from tests.utilidades import servicio_temporal


class CargaInicialTest(unittest.TestCase):
    def setUp(self):
        self.servicio, _ = servicio_temporal(self)

    def test_carga_los_quince_pokemon_y_cuatro_familias(self):
        estadisticas = self.servicio.estadisticas()
        self.assertEqual(estadisticas["total_pokemon"], 15)
        self.assertEqual(estadisticas["total_familias"], 4)
        self.assertEqual(estadisticas["total_relaciones"], 11)

    def test_etapas_de_la_linea_charmander(self):
        self.assertEqual(self.servicio.obtener(4)["etapa"], "Inicial")
        self.assertEqual(self.servicio.obtener(5)["etapa"], "Intermedia")
        self.assertEqual(self.servicio.obtener(6)["etapa"], "Final")

    def test_ficha_incluye_ruta_padre_e_hijos(self):
        ficha = self.servicio.obtener(6)
        self.assertEqual([p["nombre"] for p in ficha["ruta"]], ["Charmander", "Charmeleon", "Charizard"])
        self.assertEqual(ficha["padre"]["id"], 5)
        self.assertEqual(ficha["hijos"], [])

    def test_eevee_tiene_cinco_ramificaciones(self):
        ficha = self.servicio.obtener(133)
        self.assertEqual([hijo["id"] for hijo in ficha["hijos"]], [134, 135, 136, 196, 197])

    def test_listar_filtra_por_tipo(self):
        agua = [pokemon["nombre"] for pokemon in self.servicio.listar(tipo="Agua")]
        self.assertEqual(agua, ["Squirtle", "Wartortle", "Blastoise", "Vaporeon"])

    def test_tipo_inexistente_en_listado(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.listar(tipo="Mágico")

    def test_id_inexistente(self):
        with self.assertRaises(ErrorNoEncontrado):
            self.servicio.obtener(999)

    def test_tipos_presentes_en_orden_oficial(self):
        self.assertEqual(self.servicio.tipos()[:3], ["Normal", "Fuego", "Agua"])


class RegistroYEdicionTest(unittest.TestCase):
    def setUp(self):
        self.servicio, self.repositorio = servicio_temporal(self)

    def test_registra_pokemon_sin_evoluciones_y_persiste(self):
        self.servicio.registrar({"id": 25, "nombre": "Pikachu", "tipos": ["Eléctrico"]})
        self.assertEqual(self.servicio.obtener(25)["etapa"], "Sin evoluciones")

        recargado = PokemonService(self.repositorio)
        self.assertEqual(recargado.obtener(25)["pokemon"]["nombre"], "Pikachu")

    def test_no_permite_identificadores_duplicados(self):
        with self.assertRaises(ErrorConflicto):
            self.servicio.registrar({"id": 1, "nombre": "Otro", "tipos": ["Normal"]})

    def test_datos_invalidos_no_se_registran(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.registrar({"id": 26, "nombre": "X", "tipos": ["Normal"]})
        with self.assertRaises(ErrorNoEncontrado):
            self.servicio.obtener(26)

    def test_actualiza_descripcion_y_persiste(self):
        self.servicio.actualizar(1, {"descripcion": "Descripción nueva"})
        recargado = PokemonService(self.repositorio)
        self.assertEqual(recargado.obtener(1)["pokemon"]["descripcion"], "Descripción nueva")

    def test_actualizar_no_permite_cambiar_id(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.actualizar(1, {"id": 2})


class EvolucionesTest(unittest.TestCase):
    def setUp(self):
        self.servicio, self.repositorio = servicio_temporal(self)
        self.servicio.registrar({"id": 172, "nombre": "Pichu", "tipos": ["Eléctrico"]})
        self.servicio.registrar({"id": 25, "nombre": "Pikachu", "tipos": ["Eléctrico"]})

    def test_enlaza_pokemon_sin_evoluciones_y_persiste(self):
        self.servicio.crear_evolucion(172, 25)
        self.assertEqual(self.servicio.obtener(25)["padre"]["id"], 172)
        self.assertEqual(self.servicio.obtener(172)["etapa"], "Inicial")
        self.assertEqual(self.servicio.obtener(25)["etapa"], "Final")

        recargado = PokemonService(self.repositorio)
        self.assertEqual(recargado.obtener(172)["hijos"][0]["id"], 25)

    def test_no_permite_conectar_consigo_mismo(self):
        with self.assertRaises(ErrorConflicto):
            self.servicio.crear_evolucion(25, 25)

    def test_no_permite_mover_un_pokemon_con_evoluciones(self):
        with self.assertRaises(ErrorConflicto):
            self.servicio.crear_evolucion(25, 4)

    def test_rechaza_pokemon_que_ya_tiene_preevolucion(self):
        with self.assertRaises(ErrorConflicto):
            self.servicio.crear_evolucion(25, 5)

    def test_rechaza_ids_desconocidos(self):
        with self.assertRaises(ErrorNoEncontrado):
            self.servicio.crear_evolucion(999, 25)

    def test_rechaza_ids_que_no_son_enteros(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.crear_evolucion("172", 25)

    def test_las_etapas_se_recalculan_al_enlazar(self):
        self.assertEqual(self.servicio.obtener(172)["etapa"], "Sin evoluciones")
        self.servicio.crear_evolucion(172, 25)
        self.assertEqual(self.servicio.obtener(172)["etapa"], "Inicial")


class BusquedaYRecorridosTest(unittest.TestCase):
    def setUp(self):
        self.servicio, _ = servicio_temporal(self)

    def test_busqueda_por_nombre_con_dfs_y_bfs(self):
        for algoritmo in ("dfs", "bfs"):
            resultado = self.servicio.buscar("Eevee", algoritmo)
            self.assertTrue(resultado["encontrado"])
            self.assertEqual(resultado["pokemon"]["nombre"], "Eevee")
            self.assertEqual(resultado["algoritmo"], algoritmo)

    def test_busqueda_por_id(self):
        resultado = self.servicio.buscar("197", "bfs")
        self.assertEqual(resultado["pokemon"]["nombre"], "Umbreon")

    def test_busqueda_sin_resultados_da_mensaje_claro(self):
        resultado = self.servicio.buscar("Mewtwo", "dfs")
        self.assertFalse(resultado["encontrado"])
        self.assertIn("No se encontró", resultado["mensaje"])

    def test_busqueda_vacia_es_invalida(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.buscar("   ", "dfs")

    def test_recorrido_comparado_en_cadena_coincide(self):
        resultado = self.servicio.recorrido("comparar", raiz="Charmander")
        self.assertTrue(resultado["mismo_orden"])
        self.assertEqual([p["id"] for p in resultado["dfs"]["orden"]], [4, 5, 6])

    def test_recorrido_de_eevee_en_ambos_algoritmos(self):
        resultado = self.servicio.recorrido("dfs", raiz="133")
        self.assertEqual([p["id"] for p in resultado["orden"]], [133, 134, 135, 136, 196, 197])

    def test_recorrido_con_raiz_inexistente(self):
        with self.assertRaises(ErrorNoEncontrado):
            self.servicio.recorrido("dfs", raiz="Missingno")

    def test_recorrido_con_algoritmo_invalido(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.recorrido("dijkstra")


class DatosCorruptosTest(unittest.TestCase):
    def test_rechaza_relacion_hacia_pokemon_inexistente(self):
        servicio, repositorio = servicio_temporal(self)
        datos = repositorio.cargar()
        datos["evoluciones"].append({"padre": 1, "hijo": 999})
        repositorio.guardar(datos)
        with self.assertRaises(ErrorValidacion):
            PokemonService(repositorio)

    def test_rechaza_pokemon_con_dos_preevoluciones(self):
        _, repositorio = servicio_temporal(self)
        datos = repositorio.cargar()
        datos["evoluciones"].append({"padre": 4, "hijo": 2})  # Ivysaur ya evoluciona desde Bulbasaur
        repositorio.guardar(datos)
        with self.assertRaises(ErrorValidacion):
            PokemonService(repositorio)

    def test_rechaza_ciclos_en_los_datos(self):
        _, repositorio = servicio_temporal(self)
        datos = repositorio.cargar()
        datos["evoluciones"].append({"padre": 3, "hijo": 1})
        repositorio.guardar(datos)
        with self.assertRaises(ErrorValidacion):
            PokemonService(repositorio)

    def test_archivo_no_json_produce_error_comprensible(self):
        _, repositorio = servicio_temporal(self)
        repositorio.ruta.write_text("{ esto no es json", encoding="utf-8")
        with self.assertRaises(RuntimeError) as contexto:
            PokemonService(PokemonRepository(repositorio.ruta))
        self.assertIn("JSON válido", str(contexto.exception))

    def test_guardado_produce_json_legible(self):
        servicio, repositorio = servicio_temporal(self)
        servicio.actualizar(1, {"nombre": "Bulbasaur"})
        contenido = json.loads(repositorio.ruta.read_text(encoding="utf-8"))
        self.assertEqual(len(contenido["pokemon"]), 15)
        self.assertEqual(len(contenido["evoluciones"]), 11)


if __name__ == "__main__":
    unittest.main()
