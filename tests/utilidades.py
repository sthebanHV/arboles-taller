"""Ayudas compartidas por las pruebas: Pokémon de ejemplo y datos temporales."""

import shutil
import tempfile
from pathlib import Path

from models.pokemon import Pokemon
from repositories.pokemon_repository import RUTA_DATOS_POR_DEFECTO, PokemonRepository
from services.pokemon_service import PokemonService


def crear_pokemon(identificador, nombre, tipos=("Normal",)):
    return Pokemon(identificador, nombre, list(tipos))


def servicio_temporal(caso_de_prueba):
    """Servicio sobre una copia de data/pokemon.json que se borra al terminar la prueba."""
    directorio = tempfile.TemporaryDirectory()
    caso_de_prueba.addCleanup(directorio.cleanup)
    ruta = Path(directorio.name) / "pokemon.json"
    shutil.copy(RUTA_DATOS_POR_DEFECTO, ruta)
    repositorio = PokemonRepository(ruta)
    return PokemonService(repositorio), repositorio
