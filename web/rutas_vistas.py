"""Páginas HTML. Los datos se piden a la API desde JavaScript."""

from flask import Blueprint, current_app, redirect, render_template, url_for

from models.pokemon import TIPOS_VALIDOS

vistas = Blueprint("vistas", __name__)


@vistas.get("/")
def inicio():
    return render_template("index.html", pagina="inicio")


@vistas.get("/explorar")
def explorar_inicial():
    primero = current_app.extensions["pokedex_service"].listar()[0]["id"]
    return redirect(url_for("vistas.explorar", identificador=primero))


@vistas.get("/explorar/<int:identificador>")
def explorar(identificador):
    return render_template("detalle.html", pagina="explorar", pokemon_id=identificador)


@vistas.get("/admin")
def administrar():
    return render_template("admin.html", pagina="admin", tipos=TIPOS_VALIDOS)
