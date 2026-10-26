"""Modelo de un Pokémon con sus datos y sus reglas de validación."""

from models.errores import ErrorValidacion

TIPOS_VALIDOS = (
    "Normal", "Fuego", "Agua", "Planta", "Eléctrico", "Hielo", "Lucha",
    "Veneno", "Tierra", "Volador", "Psíquico", "Bicho", "Roca", "Fantasma",
    "Dragón", "Siniestro", "Acero", "Hada",
)

ETAPA_INICIAL = "Inicial"
ETAPA_INTERMEDIA = "Intermedia"
ETAPA_FINAL = "Final"
ETAPA_SIN_EVOLUCIONES = "Sin evoluciones"

CAMPOS_EDITABLES = ("nombre", "tipos", "descripcion", "habilidades", "imagen")


class Pokemon:
    """Datos de un Pokémon. El identificador no cambia una vez creado."""

    def __init__(
        self,
        identificador,
        nombre,
        tipos,
        descripcion="",
        habilidades=None,
        imagen="",
        nivel_evolutivo=ETAPA_SIN_EVOLUCIONES,
    ):
        self._id = self._validar_identificador(identificador)
        self._nombre = self._validar_nombre(nombre)
        self._tipos = self._validar_tipos(tipos)
        self._descripcion = self._validar_descripcion(descripcion)
        self._habilidades = self._validar_habilidades(habilidades or [])
        self._imagen = self._validar_imagen(imagen)
        self.nivel_evolutivo = nivel_evolutivo

    @property
    def id(self):
        return self._id

    @property
    def nombre(self):
        return self._nombre

    @property
    def tipos(self):
        return list(self._tipos)

    @property
    def descripcion(self):
        return self._descripcion

    @property
    def habilidades(self):
        return list(self._habilidades)

    @property
    def imagen(self):
        return self._imagen

    def tiene_tipo(self, tipo):
        return tipo in self._tipos

    def obtener_datos(self):
        """Devuelve los datos del Pokémon listos para JSON."""
        return {
            "id": self._id,
            "nombre": self._nombre,
            "tipos": self.tipos,
            "descripcion": self._descripcion,
            "habilidades": self.habilidades,
            "imagen": self._imagen,
            "nivel_evolutivo": self.nivel_evolutivo,
        }

    def actualizar(self, **campos):
        """Actualiza solo los campos editables; valida antes de asignar."""
        desconocidos = set(campos) - set(CAMPOS_EDITABLES)
        if desconocidos:
            raise ErrorValidacion(
                "Campos no editables o inexistentes: " + ", ".join(sorted(desconocidos))
            )
        validadores = {
            "nombre": self._validar_nombre,
            "tipos": self._validar_tipos,
            "descripcion": self._validar_descripcion,
            "habilidades": lambda valor: self._validar_habilidades(valor or []),
            "imagen": self._validar_imagen,
        }
        # Se validan todos primero para no dejar el objeto a medio actualizar.
        nuevos = {campo: validadores[campo](valor) for campo, valor in campos.items()}
        for campo, valor in nuevos.items():
            setattr(self, f"_{campo}", valor)

    @classmethod
    def desde_datos(cls, datos):
        """Crea un Pokémon a partir de un diccionario (JSON o formulario)."""
        if not isinstance(datos, dict):
            raise ErrorValidacion("Los datos del Pokémon deben enviarse como objeto JSON.")
        return cls(
            identificador=datos.get("id"),
            nombre=datos.get("nombre"),
            tipos=datos.get("tipos"),
            descripcion=datos.get("descripcion", ""),
            habilidades=datos.get("habilidades", []),
            imagen=datos.get("imagen", ""),
            nivel_evolutivo=datos.get("nivel_evolutivo", ETAPA_SIN_EVOLUCIONES),
        )

    @staticmethod
    def _validar_identificador(valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ErrorValidacion("El identificador debe ser un número entero positivo.")
        return valor

    @staticmethod
    def _validar_nombre(valor):
        if not isinstance(valor, str) or not 2 <= len(valor.strip()) <= 30:
            raise ErrorValidacion("El nombre debe tener entre 2 y 30 caracteres.")
        return valor.strip()

    @staticmethod
    def _validar_tipos(valor):
        if not isinstance(valor, (list, tuple)) or not 1 <= len(valor) <= 2:
            raise ErrorValidacion("Un Pokémon debe tener entre 1 y 2 tipos.")
        desconocidos = [tipo for tipo in valor if tipo not in TIPOS_VALIDOS]
        if desconocidos:
            raise ErrorValidacion("Tipos no reconocidos: " + ", ".join(map(str, desconocidos)))
        if len(set(valor)) != len(valor):
            raise ErrorValidacion("Los tipos no pueden repetirse.")
        return tuple(valor)

    @staticmethod
    def _validar_descripcion(valor):
        if not isinstance(valor, str) or len(valor) > 400:
            raise ErrorValidacion("La descripción debe ser texto de hasta 400 caracteres.")
        return valor.strip()

    @staticmethod
    def _validar_habilidades(valor):
        if not isinstance(valor, (list, tuple)) or len(valor) > 3:
            raise ErrorValidacion("Las habilidades deben ser una lista de hasta 3 elementos.")
        if not all(isinstance(habilidad, str) and habilidad.strip() for habilidad in valor):
            raise ErrorValidacion("Cada habilidad debe ser un texto no vacío.")
        return tuple(habilidad.strip() for habilidad in valor)

    @staticmethod
    def _validar_imagen(valor):
        if not isinstance(valor, str) or len(valor) > 200:
            raise ErrorValidacion("La imagen debe ser una ruta de texto relativa a static/img.")
        if valor.startswith("/") or ".." in valor:
            raise ErrorValidacion("La ruta de la imagen no puede ser absoluta ni salir de static/img.")
        return valor.strip()
