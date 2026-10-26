"""Formato único de respuestas JSON de la API.

Éxito:  {"ok": true,  "datos": ...}
Error:  {"ok": false, "error": {"codigo": "...", "mensaje": "..."}}
"""

from flask import jsonify


def exito(datos, estado=200):
    return jsonify({"ok": True, "datos": datos}), estado


def error(codigo, mensaje, estado):
    return jsonify({"ok": False, "error": {"codigo": codigo, "mensaje": mensaje}}), estado
