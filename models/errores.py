"""Excepciones de dominio con el código HTTP que les corresponde."""


class ErrorDominio(Exception):
    """Base de los errores de reglas de negocio."""

    estado = 400
    codigo = "error_dominio"

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ErrorValidacion(ErrorDominio):
    """Los datos recibidos no cumplen las reglas (400)."""

    estado = 400
    codigo = "validacion"


class ErrorNoEncontrado(ErrorDominio):
    """El Pokémon o el recurso solicitado no existe (404)."""

    estado = 404
    codigo = "no_encontrado"


class ErrorConflicto(ErrorDominio):
    """La operación contradice el estado actual: duplicados, ciclos, etc. (409)."""

    estado = 409
    codigo = "conflicto"
