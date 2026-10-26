"""Endpoints REST. Solo traducen HTTP a llamadas del servicio y de vuelta."""

from flask import Blueprint, current_app, request

from models.errores import ErrorValidacion
from web.respuestas import exito

api = Blueprint("api", __name__, url_prefix="/api")


def servicio():
    return current_app.extensions["pokedex_service"]


def cuerpo_json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorValidacion("El cuerpo de la petición debe ser un objeto JSON válido.")
    return datos


@api.get("/pokemon")
def listar_pokemon():
    return exito(servicio().listar(tipo=request.args.get("tipo")))


@api.post("/pokemon")
def registrar_pokemon():
    return exito(servicio().registrar(cuerpo_json()), estado=201)


@api.get("/pokemon/<int:identificador>")
def obtener_pokemon(identificador):
    return exito(servicio().obtener(identificador))


@api.put("/pokemon/<int:identificador>")
def actualizar_pokemon(identificador):
    return exito(servicio().actualizar(identificador, cuerpo_json()))


@api.get("/pokemon/<int:identificador>/evoluciones")
def evoluciones_pokemon(identificador):
    return exito(servicio().evoluciones(identificador))


@api.post("/evoluciones")
def crear_evolucion():
    datos = cuerpo_json()
    return exito(
        servicio().crear_evolucion(datos.get("padre_id"), datos.get("hijo_id")),
        estado=201,
    )


@api.get("/buscar")
def buscar():
    return exito(
        servicio().buscar(request.args.get("q"), request.args.get("algoritmo", "dfs"))
    )


@api.get("/recorrido")
def recorrido():
    return exito(
        servicio().recorrido(
            algoritmo=request.args.get("algoritmo", "dfs"),
            raiz=request.args.get("raiz") or None,
        )
    )


@api.get("/tipos")
def tipos():
    return exito(servicio().tipos())


@api.get("/estadisticas")
def estadisticas():
    return exito(servicio().estadisticas())
