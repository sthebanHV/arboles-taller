"""Punto de entrada de PokéDex Explorer.

Uso:  python app.py   (o `flask --app app run --debug`)
"""

import logging

from flask import Flask, request
from werkzeug.exceptions import HTTPException

from models.errores import ErrorDominio
from services.pokemon_service import PokemonService
from web.respuestas import error
from web.rutas_api import api
from web.rutas_vistas import vistas

logger = logging.getLogger(__name__)


def create_app(servicio=None):
    """Fábrica de la aplicación. Los tests pasan un servicio con datos temporales."""
    app = Flask(__name__)
    app.extensions["pokedex_service"] = servicio or PokemonService()
    app.register_blueprint(vistas)
    app.register_blueprint(api)
    _registrar_manejadores_de_error(app)
    return app


def _registrar_manejadores_de_error(app):
    @app.errorhandler(ErrorDominio)
    def error_de_dominio(excepcion):
        return error(excepcion.codigo, excepcion.mensaje, excepcion.estado)

    @app.errorhandler(HTTPException)
    def error_http(excepcion):
        if not request.path.startswith("/api/"):
            return excepcion
        codigos = {404: "no_encontrado", 405: "metodo_no_permitido"}
        mensajes = {
            404: "La ruta solicitada no existe.",
            405: "El método HTTP no está permitido para esta ruta.",
        }
        return error(
            codigos.get(excepcion.code, "peticion_invalida"),
            mensajes.get(excepcion.code, "La petición no es válida."),
            excepcion.code,
        )

    @app.errorhandler(Exception)
    def error_inesperado(excepcion):
        # El detalle técnico se registra en el servidor; el cliente solo ve un mensaje genérico.
        logger.exception("Error inesperado en %s", request.path)
        if not request.path.startswith("/api/"):
            return "Ocurrió un error interno. Intenta de nuevo.", 500
        return error("error_interno", "Ocurrió un error interno. Intenta de nuevo.", 500)


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
