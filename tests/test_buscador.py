"""Pruebas de DFS y BFS: orden de visita, búsqueda y comparación."""

import unittest

from models.arbol_evolucion import ArbolEvolucion
from models.errores import ErrorValidacion
from services.buscador import Buscador, normalizar_texto
from tests.utilidades import crear_pokemon


def arbol_ramificado():
    """
           1 Alfa
         /       \\
     2 Beta     3 Gamma
     /    \\         \\
  4 Delta 5 Épsilon  6 Zeta
    """
    arbol = ArbolEvolucion()
    arbol.establecer_raiz(crear_pokemon(1, "Alfa"))
    arbol.conectar(1, crear_pokemon(2, "Beta"))
    arbol.conectar(1, crear_pokemon(3, "Gamma"))
    arbol.conectar(2, crear_pokemon(4, "Delta"))
    arbol.conectar(2, crear_pokemon(5, "Épsilon"))
    arbol.conectar(3, crear_pokemon(6, "Zeta"))
    return arbol


class RecorridoCompletoTest(unittest.TestCase):
    def setUp(self):
        self.buscador = Buscador()
        self.raiz = arbol_ramificado().raiz

    def test_dfs_visita_en_profundidad(self):
        resultado = self.buscador.dfs(self.raiz)
        self.assertEqual(resultado.ids(), [1, 2, 4, 5, 3, 6])
        self.assertIsNone(resultado.encontrado)

    def test_bfs_visita_por_niveles(self):
        resultado = self.buscador.bfs(self.raiz)
        self.assertEqual(resultado.ids(), [1, 2, 3, 4, 5, 6])
        self.assertIsNone(resultado.encontrado)

    def test_dfs_y_bfs_difieren_en_arboles_ramificados(self):
        comparacion = self.buscador.comparar([self.raiz])
        self.assertNotEqual(comparacion["dfs"].ids(), comparacion["bfs"].ids())

    def test_recorrido_de_lineas_sin_ramas_coincide(self):
        arbol = ArbolEvolucion()
        arbol.establecer_raiz(crear_pokemon(4, "Charmander"))
        arbol.conectar(4, crear_pokemon(5, "Charmeleon"))
        arbol.conectar(5, crear_pokemon(6, "Charizard"))
        comparacion = self.buscador.comparar([arbol.raiz])
        self.assertEqual(comparacion["dfs"].ids(), comparacion["bfs"].ids())

    def test_recorrido_de_varias_familias_en_orden(self):
        otra = ArbolEvolucion()
        otra.establecer_raiz(crear_pokemon(7, "Squirtle"))
        resultado = self.buscador.recorrer([self.raiz, otra.raiz], "bfs")
        self.assertEqual(resultado.ids(), [1, 2, 3, 4, 5, 6, 7])

    def test_recorrido_de_subarbol(self):
        arbol = arbol_ramificado()
        resultado = self.buscador.dfs(arbol.obtener_nodo(2))
        self.assertEqual(resultado.ids(), [2, 4, 5])


class BusquedaTest(unittest.TestCase):
    def setUp(self):
        self.buscador = Buscador()
        self.raiz = arbol_ramificado().raiz

    def test_dfs_encuentra_por_id_y_detiene_la_busqueda(self):
        resultado = self.buscador.buscar([self.raiz], 5, "dfs")
        self.assertEqual(resultado.encontrado.id, 5)
        self.assertEqual(resultado.ids(), [1, 2, 4, 5])

    def test_bfs_encuentra_por_id_con_otro_orden(self):
        resultado = self.buscador.buscar([self.raiz], 5, "bfs")
        self.assertEqual(resultado.encontrado.id, 5)
        self.assertEqual(resultado.ids(), [1, 2, 3, 4, 5])

    def test_busqueda_por_nombre_ignora_acentos_y_mayusculas(self):
        resultado = self.buscador.buscar([self.raiz], "EPSILON", "bfs")
        self.assertEqual(resultado.encontrado.id, 5)
        self.assertEqual(resultado.encontrado.pokemon.nombre, "Épsilon")

    def test_busqueda_sin_coincidencias_recorre_todo(self):
        resultado = self.buscador.buscar([self.raiz], "Omega", "dfs")
        self.assertIsNone(resultado.encontrado)
        self.assertEqual(len(resultado.orden), 6)

    def test_algoritmo_desconocido(self):
        with self.assertRaises(ErrorValidacion):
            self.buscador.buscar([self.raiz], 1, "astar")

    def test_normalizar_texto(self):
        self.assertEqual(normalizar_texto("  Épsilon  "), "epsilon")


if __name__ == "__main__":
    unittest.main()
