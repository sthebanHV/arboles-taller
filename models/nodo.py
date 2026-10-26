"""Nodo de un árbol de evolución: un Pokémon con su padre y sus hijos."""

from models.errores import ErrorConflicto
from models.pokemon import (
    ETAPA_FINAL,
    ETAPA_INICIAL,
    ETAPA_INTERMEDIA,
    ETAPA_SIN_EVOLUCIONES,
)


class Nodo:
    def __init__(self, pokemon):
        self._pokemon = pokemon
        self._padre = None
        self._hijos = []

    @property
    def pokemon(self):
        return self._pokemon

    @property
    def id(self):
        return self._pokemon.id

    @property
    def padre(self):
        return self._padre

    @property
    def hijos(self):
        """Copia de la lista de hijos para que nadie la modifique desde fuera."""
        return list(self._hijos)

    def agregar_hijo(self, hijo):
        """Enlaza un nodo como descendiente directo. Un nodo tiene un único padre."""
        if hijo is self:
            raise ErrorConflicto("Un Pokémon no puede evolucionar en sí mismo.")
        if hijo.padre is not None:
            raise ErrorConflicto(
                f"{hijo.pokemon.nombre} ya tiene una preevolución registrada."
            )
        hijo._padre = self
        self._hijos.append(hijo)

    def es_raiz(self):
        return self._padre is None

    def es_hoja(self):
        return not self._hijos

    def ancestros(self):
        """Padres desde el inmediato hasta la raíz, sin incluir este nodo."""
        resultado = []
        actual = self._padre
        while actual is not None:
            resultado.append(actual)
            actual = actual.padre
        return resultado

    def profundidad(self):
        return len(self.ancestros())

    def etapa(self):
        """Calcula la etapa evolutiva según la posición en el árbol."""
        if self.es_raiz() and self.es_hoja():
            return ETAPA_SIN_EVOLUCIONES
        if self.es_raiz():
            return ETAPA_INICIAL
        if self.es_hoja():
            return ETAPA_FINAL
        return ETAPA_INTERMEDIA
