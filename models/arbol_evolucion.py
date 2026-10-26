"""Árbol de evolución: una familia de Pokémon con una única raíz.

Cada familia (por ejemplo Charmander → Charmeleon → Charizard) es un árbol.
Las ramificaciones (Eevee → Vaporeon, Jolteon, ...) son hijos de un mismo padre.
"""

from models.errores import ErrorConflicto, ErrorNoEncontrado
from models.nodo import Nodo


class ArbolEvolucion:
    def __init__(self):
        self._raiz = None
        self._nodos = {}

    @property
    def raiz(self):
        return self._raiz

    @property
    def tamano(self):
        return len(self._nodos)

    def __len__(self):
        return len(self._nodos)

    def __contains__(self, identificador):
        return identificador in self._nodos

    def nodos(self):
        """Todos los nodos en el orden en que se insertaron."""
        return list(self._nodos.values())

    def obtener_nodo(self, identificador):
        """Devuelve el nodo con ese id o lanza ErrorNoEncontrado."""
        nodo = self._nodos.get(identificador)
        if nodo is None:
            raise ErrorNoEncontrado(
                f"El Pokémon {identificador} no pertenece a este árbol de evolución."
            )
        return nodo

    def establecer_raiz(self, pokemon):
        """Crea la raíz. Solo se puede hacer sobre un árbol vacío."""
        if self._raiz is not None:
            raise ErrorConflicto("El árbol ya tiene raíz; usa conectar() para agregar evoluciones.")
        nodo = Nodo(pokemon)
        self._raiz = nodo
        self._nodos[pokemon.id] = nodo
        self._refrescar_etapa(nodo)
        return nodo

    def conectar(self, padre_id, pokemon):
        """Inserta `pokemon` como evolución directa de `padre_id`.

        Valida que el padre exista, que no sea el mismo Pokémon, que el id no
        esté repetido y que la nueva conexión no cree un ciclo.
        """
        if self._raiz is None:
            raise ErrorConflicto("El árbol no tiene raíz; establece una antes de conectar evoluciones.")
        padre = self.obtener_nodo(padre_id)
        if pokemon.id == padre_id:
            raise ErrorConflicto("Un Pokémon no puede evolucionar en sí mismo.")
        if pokemon.id in self._nodos:
            raise ErrorConflicto(f"El Pokémon {pokemon.id} ya existe en este árbol.")
        self._validar_sin_ciclo(padre, pokemon.id)

        nodo = Nodo(pokemon)
        padre.agregar_hijo(nodo)
        self._nodos[pokemon.id] = nodo
        # Solo cambian la etapa del padre y la del nuevo nodo; el resto no se ve afectado.
        self._refrescar_etapa(padre)
        self._refrescar_etapa(nodo)
        return nodo

    def padre(self, identificador):
        return self.obtener_nodo(identificador).padre

    def hijos(self, identificador):
        return self.obtener_nodo(identificador).hijos

    def descendientes(self, identificador):
        """Todos los nodos bajo `identificador` (sin incluirlo), en preorden.

        Usa una pila explícita para no depender de la profundidad de la recursión.
        """
        pila = list(reversed(self.obtener_nodo(identificador).hijos))
        resultado = []
        while pila:
            actual = pila.pop()
            resultado.append(actual)
            pila.extend(reversed(actual.hijos))
        return resultado

    def ruta_desde_raiz(self, identificador):
        """Lista de Pokémon desde la raíz hasta `identificador`, ambos incluidos."""
        nodo = self.obtener_nodo(identificador)
        ruta = [nodo.pokemon] + [ancestro.pokemon for ancestro in nodo.ancestros()]
        return list(reversed(ruta))

    def a_diccionario(self, identificador=None):
        """Representación anidada del (sub)árbol, lista para la visualización."""
        nodo = self._raiz if identificador is None else self.obtener_nodo(identificador)
        if nodo is None:
            return None
        return self._nodo_a_diccionario(nodo)

    def _nodo_a_diccionario(self, nodo):
        pokemon = nodo.pokemon
        return {
            "id": pokemon.id,
            "nombre": pokemon.nombre,
            "tipos": pokemon.tipos,
            "imagen": pokemon.imagen,
            "etapa": nodo.etapa(),
            "hijos": [self._nodo_a_diccionario(hijo) for hijo in nodo.hijos],
        }

    def _validar_sin_ciclo(self, padre, identificador_hijo):
        if any(ancestro.id == identificador_hijo for ancestro in padre.ancestros() + [padre]):
            raise ErrorConflicto("Esta conexión crearía un ciclo en la línea evolutiva.")

    @staticmethod
    def _refrescar_etapa(nodo):
        nodo.pokemon.nivel_evolutivo = nodo.etapa()
