"""Algoritmos de recorrido sobre los árboles de evolución: DFS y BFS.

Todos los recorridos se ejecutan aquí, en Python. JavaScript solo pide
resultados a la API y los muestra.

Complejidad (N = nodos visitados, H = altura del árbol, A = ancho máximo):
- DFS: tiempo O(N), espacio O(H) en la pila explícita.
- BFS: tiempo O(N), espacio O(A) en la cola.
- Búsqueda: en el peor caso recorre todos los nodos, O(N).
"""

import unicodedata
from collections import deque
from dataclasses import dataclass

from models.errores import ErrorValidacion

ALGORITMOS = ("dfs", "bfs")


def normalizar_texto(texto):
    """Minúsculas, sin acentos y con espacios simples, para comparar nombres."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))
    return " ".join(sin_acentos.lower().split())


@dataclass
class ResultadoRecorrido:
    """Orden de visita de un recorrido y, si se buscaba algo, el nodo hallado."""

    algoritmo: str
    orden: list
    encontrado: object = None

    def ids(self):
        return [nodo.id for nodo in self.orden]


class Buscador:
    """Implementa DFS y BFS sobre nodos de un árbol de evolución."""

    def dfs(self, inicio, predicado=None):
        """Búsqueda en profundidad (preorden) con pila explícita.

        Si `predicado` es None, recorre el subárbol completo.
        """
        pila = [inicio]
        orden = []
        while pila:
            actual = pila.pop()
            orden.append(actual)
            if predicado is not None and predicado(actual):
                return ResultadoRecorrido("dfs", orden, actual)
            # Se apilan en orden inverso para visitar primero al hijo más antiguo.
            pila.extend(reversed(actual.hijos))
        return ResultadoRecorrido("dfs", orden, None)

    def bfs(self, inicio, predicado=None):
        """Búsqueda en anchura por niveles, con una cola (deque)."""
        cola = deque([inicio])
        orden = []
        while cola:
            actual = cola.popleft()
            orden.append(actual)
            if predicado is not None and predicado(actual):
                return ResultadoRecorrido("bfs", orden, actual)
            cola.extend(actual.hijos)
        return ResultadoRecorrido("bfs", orden, None)

    def recorrer(self, inicios, algoritmo):
        """Recorrido completo de cada árbol indicado, en orden."""
        return self._recorrer(inicios, algoritmo, predicado=None)

    def buscar(self, inicios, criterio, algoritmo):
        """Busca por id (int) o por nombre (texto) y se detiene al encontrarlo."""
        return self._recorrer(inicios, algoritmo, self.crear_predicado(criterio))

    def comparar(self, inicios, criterio=None):
        """Ejecuta DFS y BFS sobre los mismos nodos para contrastar los resultados."""
        return {
            "dfs": self._recorrer(inicios, "dfs", self.crear_predicado(criterio)),
            "bfs": self._recorrer(inicios, "bfs", self.crear_predicado(criterio)),
        }

    @staticmethod
    def crear_predicado(criterio):
        if criterio is None:
            return None
        if isinstance(criterio, int):
            return lambda nodo: nodo.id == criterio
        texto = normalizar_texto(criterio)
        return lambda nodo: normalizar_texto(nodo.pokemon.nombre) == texto

    def _recorrer(self, inicios, algoritmo, predicado):
        if algoritmo not in ALGORITMOS:
            raise ErrorValidacion("El algoritmo debe ser 'dfs' o 'bfs'.")
        ejecutar = self.dfs if algoritmo == "dfs" else self.bfs
        orden_total = []
        for inicio in inicios:
            resultado = ejecutar(inicio, predicado)
            orden_total.extend(resultado.orden)
            if resultado.encontrado is not None:
                return ResultadoRecorrido(algoritmo, orden_total, resultado.encontrado)
        return ResultadoRecorrido(algoritmo, orden_total, None)
