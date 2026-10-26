"""Persistencia de los Pokémon y sus relaciones en un archivo JSON."""

import json
import os
import tempfile
from pathlib import Path

RUTA_DATOS_POR_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "pokemon.json"
VERSION_FORMATO = 1


class PokemonRepository:
    """Lee y escribe `data/pokemon.json`.

    El formato guarda dos listas: `pokemon` (datos de cada uno) y `evoluciones`
    (pares padre/hijo). El árbol se reconstruye al cargar, no se guarda anidado.
    """

    def __init__(self, ruta=RUTA_DATOS_POR_DEFECTO):
        self._ruta = Path(ruta)

    @property
    def ruta(self):
        return self._ruta

    def cargar(self):
        if not self._ruta.exists():
            raise RuntimeError(f"No se encontró el archivo de datos: {self._ruta}")
        try:
            with open(self._ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"El archivo de datos no es JSON válido: {error}") from error
        return {
            "pokemon": datos.get("pokemon", []),
            "evoluciones": datos.get("evoluciones", []),
        }

    def guardar(self, datos):
        """Escribe el archivo de forma atómica: primero un temporal, luego reemplazo.

        Así un corte de energía o un error a mitad de escritura no deja el JSON roto.
        """
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(
            dir=self._ruta.parent, prefix=".pokemon-", suffix=".tmp"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                json.dump(
                    {
                        "version": VERSION_FORMATO,
                        "pokemon": datos["pokemon"],
                        "evoluciones": datos["evoluciones"],
                    },
                    archivo,
                    ensure_ascii=False,
                    indent=2,
                )
                archivo.flush()
                os.fsync(archivo.fileno())
            os.replace(temporal, self._ruta)
        except BaseException:
            if os.path.exists(temporal):
                os.remove(temporal)
            raise
