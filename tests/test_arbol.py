"""Pruebas del árbol de evolución: estructura, validaciones y consultas."""

import unittest

from models.arbol_evolucion import ArbolEvolucion
from models.errores import ErrorConflicto, ErrorNoEncontrado, ErrorValidacion
from models.nodo import Nodo
from models.pokemon import ETAPA_FINAL, ETAPA_INICIAL, ETAPA_INTERMEDIA, ETAPA_SIN_EVOLUCIONES
from tests.utilidades import crear_pokemon


def arbol_charmander():
    """Charmander → Charmeleon → Charizard."""
    arbol = ArbolEvolucion()
    arbol.establecer_raiz(crear_pokemon(4, "Charmander", ["Fuego"]))
    arbol.conectar(4, crear_pokemon(5, "Charmeleon", ["Fuego"]))
    arbol.conectar(5, crear_pokemon(6, "Charizard", ["Fuego", "Volador"]))
    return arbol


def arbol_eevee():
    """Eevee con cinco ramificaciones directas."""
    arbol = ArbolEvolucion()
    arbol.establecer_raiz(crear_pokemon(133, "Eevee"))
    for identificador, nombre in [(134, "Vaporeon"), (135, "Jolteon"), (136, "Flareon"),
                                  (196, "Espeon"), (197, "Umbreon")]:
        arbol.conectar(133, crear_pokemon(identificador, nombre))
    return arbol


class InsercionYRaizTest(unittest.TestCase):
    def test_establecer_raiz_crea_nodo_sin_padre(self):
        arbol = ArbolEvolucion()
        raiz = arbol.establecer_raiz(crear_pokemon(1, "Bulbasaur", ["Planta"]))
        self.assertIs(arbol.raiz, raiz)
        self.assertTrue(raiz.es_raiz())
        self.assertEqual(len(arbol), 1)

    def test_no_permite_segunda_raiz(self):
        arbol = ArbolEvolucion()
        arbol.establecer_raiz(crear_pokemon(1, "Bulbasaur"))
        with self.assertRaises(ErrorConflicto):
            arbol.establecer_raiz(crear_pokemon(2, "Ivysaur"))

    def test_conectar_sin_raiz_falla(self):
        with self.assertRaises(ErrorConflicto):
            ArbolEvolucion().conectar(1, crear_pokemon(2, "Ivysaur"))

    def test_conectar_registra_padre_e_hijos(self):
        arbol = arbol_charmander()
        self.assertEqual([nodo.id for nodo in arbol.hijos(4)], [5])
        self.assertEqual(arbol.padre(6).id, 5)
        self.assertEqual(arbol.tamano, 3)

    def test_rechaza_duplicados(self):
        arbol = arbol_charmander()
        with self.assertRaises(ErrorConflicto):
            arbol.conectar(4, crear_pokemon(6, "Charizard"))

    def test_rechaza_conectar_consigo_mismo(self):
        arbol = arbol_charmander()
        with self.assertRaises(ErrorConflicto):
            arbol.conectar(4, crear_pokemon(4, "Charmander"))

    def test_rechaza_padre_que_no_pertenece_al_arbol(self):
        with self.assertRaises(ErrorNoEncontrado):
            arbol_charmander().conectar(999, crear_pokemon(7, "Squirtle"))

    def test_no_permite_reinsertar_un_ancestro(self):
        """Intentar cerrar el ciclo Charizard → Charmander se rechaza y el árbol no cambia."""
        arbol = arbol_charmander()
        with self.assertRaises(ErrorConflicto):
            arbol.conectar(6, crear_pokemon(4, "Charmander"))
        self.assertEqual(len(arbol), 3)
        self.assertIsNone(arbol.raiz.padre)

    def test_nodo_no_acepta_segundo_padre(self):
        padre_a = Nodo(crear_pokemon(1, "Alfa"))
        padre_b = Nodo(crear_pokemon(2, "Beta"))
        hijo = Nodo(crear_pokemon(3, "Gamma"))
        padre_a.agregar_hijo(hijo)
        with self.assertRaises(ErrorConflicto):
            padre_b.agregar_hijo(hijo)


class EtapasYConsultasTest(unittest.TestCase):
    def test_etapas_segun_posicion(self):
        arbol = arbol_charmander()
        self.assertEqual(arbol.obtener_nodo(4).etapa(), ETAPA_INICIAL)
        self.assertEqual(arbol.obtener_nodo(5).etapa(), ETAPA_INTERMEDIA)
        self.assertEqual(arbol.obtener_nodo(6).etapa(), ETAPA_FINAL)

    def test_pokemon_sin_evoluciones(self):
        arbol = ArbolEvolucion()
        arbol.establecer_raiz(crear_pokemon(132, "Ditto"))
        self.assertEqual(arbol.obtener_nodo(132).etapa(), ETAPA_SIN_EVOLUCIONES)
        self.assertEqual(arbol.obtener_nodo(132).pokemon.nivel_evolutivo, ETAPA_SIN_EVOLUCIONES)

    def test_nivel_evolutivo_del_pokemon_se_actualiza(self):
        arbol = arbol_charmander()
        self.assertEqual(arbol.obtener_nodo(6).pokemon.nivel_evolutivo, ETAPA_FINAL)
        self.assertEqual(arbol.obtener_nodo(5).pokemon.nivel_evolutivo, ETAPA_INTERMEDIA)
        self.assertEqual(arbol.obtener_nodo(4).pokemon.nivel_evolutivo, ETAPA_INICIAL)

    def test_ruta_desde_raiz(self):
        ruta = arbol_charmander().ruta_desde_raiz(6)
        self.assertEqual([pokemon.nombre for pokemon in ruta], ["Charmander", "Charmeleon", "Charizard"])

    def test_ruta_de_la_raiz_es_ella_misma(self):
        ruta = arbol_charmander().ruta_desde_raiz(4)
        self.assertEqual([pokemon.id for pokemon in ruta], [4])

    def test_descendientes_en_preorden(self):
        arbol = arbol_eevee()
        ids = [nodo.id for nodo in arbol.descendientes(133)]
        self.assertEqual(ids, [134, 135, 136, 196, 197])

    def test_descendientes_de_hoja_esta_vacio(self):
        self.assertEqual(arbol_charmander().descendientes(6), [])

    def test_consulta_de_id_inexistente(self):
        with self.assertRaises(ErrorNoEncontrado):
            arbol_charmander().obtener_nodo(999)

    def test_diccionario_anidado_para_la_visualizacion(self):
        datos = arbol_charmander().a_diccionario()
        self.assertEqual(datos["nombre"], "Charmander")
        self.assertEqual(datos["hijos"][0]["hijos"][0]["etapa"], ETAPA_FINAL)


class ValidacionDePokemonTest(unittest.TestCase):
    def test_tipo_desconocido(self):
        with self.assertRaises(ErrorValidacion):
            crear_pokemon(1, "Bulbasaur", ["Planta", "Mágico"])

    def test_mas_de_dos_tipos(self):
        with self.assertRaises(ErrorValidacion):
            crear_pokemon(1, "Bulbasaur", ["Planta", "Veneno", "Fuego"])

    def test_identificador_no_positivo(self):
        with self.assertRaises(ErrorValidacion):
            crear_pokemon(0, "Bulbasaur")

    def test_actualizar_rechaza_campos_no_editables(self):
        pokemon = crear_pokemon(1, "Bulbasaur", ["Planta"])
        with self.assertRaises(ErrorValidacion):
            pokemon.actualizar(id=2)

    def test_actualizar_es_todo_o_nada(self):
        pokemon = crear_pokemon(1, "Bulbasaur", ["Planta"])
        with self.assertRaises(ErrorValidacion):
            pokemon.actualizar(descripcion="Nueva", tipos=["Inexistente"])
        self.assertEqual(pokemon.descripcion, "")


if __name__ == "__main__":
    unittest.main()
