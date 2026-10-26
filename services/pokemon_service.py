"""Reglas de negocio del catálogo: consultas, altas, ediciones y evoluciones.

Las rutas de Flask llaman a esta clase y nunca tocan los modelos directamente.
"""

import threading
from collections import Counter, defaultdict, deque

from models.arbol_evolucion import ArbolEvolucion
from models.errores import ErrorConflicto, ErrorNoEncontrado, ErrorValidacion
from models.pokemon import ETAPA_FINAL, ETAPA_INICIAL, ETAPA_INTERMEDIA, ETAPA_SIN_EVOLUCIONES, TIPOS_VALIDOS, Pokemon
from repositories.pokemon_repository import PokemonRepository
from services.buscador import ALGORITMOS, Buscador, ResultadoRecorrido


class PokemonService:
    def __init__(self, repositorio=None, buscador=None):
        self._repositorio = repositorio or PokemonRepository()
        self._buscador = buscador or Buscador()
        self._lock = threading.RLock()
        self._familias = []
        self._familia_por_id = {}
        self._cargar()

    # ----- Consultas -------------------------------------------------------

    def listar(self, tipo=None):
        """Catálogo ordenado por id, filtrable por tipo."""
        if tipo is not None and tipo not in TIPOS_VALIDOS:
            raise ErrorValidacion(f"El tipo '{tipo}' no existe.")
        with self._lock:
            return [
                self._resumen(pokemon)
                for pokemon in self._pokemon_ordenados()
                if tipo is None or pokemon.tiene_tipo(tipo)
            ]

    def obtener(self, identificador):
        """Ficha completa: datos, padre, hijos, ruta desde la raíz y familia."""
        with self._lock:
            arbol = self._familia_de(identificador)
            nodo = arbol.obtener_nodo(identificador)
            return {
                "pokemon": self._ficha(nodo.pokemon),
                "padre": self._resumen(nodo.padre.pokemon) if nodo.padre else None,
                "hijos": [self._resumen(hijo.pokemon) for hijo in nodo.hijos],
                "ruta": [self._resumen(pokemon) for pokemon in arbol.ruta_desde_raiz(identificador)],
                "etapa": nodo.etapa(),
                "familia": {"raiz_id": arbol.raiz.id, "tamano": arbol.tamano},
                "tiene_evoluciones": arbol.tamano > 1,
            }

    def evoluciones(self, identificador):
        """Árbol anidado de la familia del Pokémon, listo para dibujar."""
        with self._lock:
            arbol = self._familia_de(identificador)
            return {
                "seleccionado_id": identificador,
                "raiz_id": arbol.raiz.id,
                "tiene_evoluciones": arbol.tamano > 1,
                "arbol": arbol.a_diccionario(),
            }

    def tipos(self):
        """Tipos presentes en el catálogo, en el orden oficial de TIPOS_VALIDOS."""
        with self._lock:
            presentes = {tipo for pokemon in self._pokemon_ordenados() for tipo in pokemon.tipos}
            return [tipo for tipo in TIPOS_VALIDOS if tipo in presentes]

    def estadisticas(self):
        with self._lock:
            pokemon = self._pokemon_ordenados()
            etapas = Counter(p.nivel_evolutivo for p in pokemon)
            tipos = Counter(tipo for p in pokemon for tipo in p.tipos)
            return {
                "total_pokemon": len(pokemon),
                "total_relaciones": sum(arbol.tamano - 1 for arbol in self._familias),
                "total_familias": len(self._familias),
                "familias_con_evoluciones": sum(1 for arbol in self._familias if arbol.tamano > 1),
                "profundidad_maxima": max(
                    (nodo.profundidad() for arbol in self._familias for nodo in arbol.nodos()),
                    default=0,
                ),
                "etapas": {etapa: etapas.get(etapa, 0) for etapa in (
                    ETAPA_INICIAL, ETAPA_INTERMEDIA, ETAPA_FINAL, ETAPA_SIN_EVOLUCIONES
                )},
                "tipos": {tipo: tipos[tipo] for tipo in TIPOS_VALIDOS if tipos[tipo]},
            }

    # ----- Búsqueda y recorridos (DFS / BFS) --------------------------------

    def buscar(self, consulta, algoritmo="dfs"):
        """Busca un Pokémon por id o por nombre usando DFS o BFS."""
        texto = (consulta or "").strip()
        if not texto:
            raise ErrorValidacion("Escribe un nombre o un identificador para buscar.")
        self._validar_algoritmo(algoritmo)
        criterio = int(texto) if texto.isdigit() else texto
        with self._lock:
            resultado = self._buscador.buscar(self._raices(), criterio, algoritmo)
            return self._respuesta_busqueda(resultado, texto)

    def recorrido(self, algoritmo="dfs", raiz=None):
        """Recorrido completo del catálogo o del subárbol de `raiz`.

        `algoritmo` puede ser 'dfs', 'bfs' o 'comparar' (ejecuta ambos).
        """
        if algoritmo != "comparar":
            self._validar_algoritmo(algoritmo)
        with self._lock:
            inicios = self._raices() if raiz is None else [self._nodo_por_consulta(raiz)]
            if algoritmo == "comparar":
                resultados = self._buscador.comparar(inicios)
                dfs, bfs = resultados["dfs"], resultados["bfs"]
                return {
                    "algoritmo": "comparar",
                    "raiz": raiz,
                    "dfs": self._respuesta_recorrido(dfs),
                    "bfs": self._respuesta_recorrido(bfs),
                    "mismo_orden": dfs.ids() == bfs.ids(),
                }
            return self._respuesta_recorrido(self._buscador.recorrer(inicios, algoritmo), raiz)

    # ----- Altas y ediciones ------------------------------------------------

    def registrar(self, datos):
        """Crea un Pokémon sin evoluciones. Su id no puede repetirse."""
        pokemon = Pokemon.desde_datos(datos)
        with self._lock:
            if pokemon.id in self._familia_por_id:
                raise ErrorConflicto(f"Ya existe un Pokémon con el id {pokemon.id}.")
            arbol = ArbolEvolucion()
            arbol.establecer_raiz(pokemon)
            self._registrar_familia(arbol)
            self._persistir()
            return self._resumen(pokemon)

    def actualizar(self, identificador, datos):
        """Edita los campos permitidos de un Pokémon existente."""
        if not isinstance(datos, dict) or not datos:
            raise ErrorValidacion("Envía al menos un campo para actualizar.")
        with self._lock:
            pokemon = self._familia_de(identificador).obtener_nodo(identificador).pokemon
            pokemon.actualizar(**datos)
            self._persistir()
            return self._ficha(pokemon)

    def crear_evolucion(self, padre_id, hijo_id):
        """Hace que `hijo_id` evolucione a partir de `padre_id`.

        Solo se enlazan Pokémon sin evoluciones previas, así no se fusionan
        familias existentes ni se generan estructuras incompatibles.
        """
        if not isinstance(padre_id, int) or not isinstance(hijo_id, int):
            raise ErrorValidacion("Los identificadores de padre e hijo deben ser números enteros.")
        if padre_id == hijo_id:
            raise ErrorConflicto("Un Pokémon no puede evolucionar en sí mismo.")
        with self._lock:
            arbol_padre = self._familia_de(padre_id)
            arbol_hijo = self._familia_de(hijo_id)
            if arbol_hijo.tamano > 1:
                raise ErrorConflicto(
                    "Ese Pokémon ya tiene evoluciones registradas y no puede enlazarse como evolución."
                )
            pokemon_hijo = arbol_hijo.raiz.pokemon
            arbol_padre.conectar(padre_id, pokemon_hijo)
            self._familias.remove(arbol_hijo)
            self._familia_por_id[hijo_id] = arbol_padre
            self._persistir()
            return {
                "padre": self._resumen(arbol_padre.obtener_nodo(padre_id).pokemon),
                "hijo": self._resumen(pokemon_hijo),
            }

    # ----- Carga y persistencia --------------------------------------------

    def _cargar(self):
        datos = self._repositorio.cargar()
        pokemon_por_id = {}
        for registro in datos["pokemon"]:
            pokemon = Pokemon.desde_datos(registro)
            if pokemon.id in pokemon_por_id:
                raise ErrorValidacion(f"Id duplicado en los datos: {pokemon.id}.")
            pokemon_por_id[pokemon.id] = pokemon

        padre_de = {}
        hijos_de = defaultdict(list)
        for relacion in datos["evoluciones"]:
            padre_id, hijo_id = relacion["padre"], relacion["hijo"]
            if padre_id not in pokemon_por_id or hijo_id not in pokemon_por_id:
                raise ErrorValidacion(f"La relación {padre_id} → {hijo_id} apunta a un Pokémon inexistente.")
            if hijo_id in padre_de:
                raise ErrorValidacion(f"El Pokémon {hijo_id} tiene más de una preevolución en los datos.")
            padre_de[hijo_id] = padre_id
            hijos_de[padre_id].append(hijo_id)

        for identificador, pokemon in sorted(pokemon_por_id.items()):
            if identificador in padre_de:
                continue
            arbol = ArbolEvolucion()
            arbol.establecer_raiz(pokemon)
            cola = deque([identificador])
            while cola:
                actual = cola.popleft()
                for hijo_id in hijos_de[actual]:
                    arbol.conectar(actual, pokemon_por_id[hijo_id])
                    cola.append(hijo_id)
            self._registrar_familia(arbol)

        if len(self._familia_por_id) != len(pokemon_por_id):
            raise ErrorValidacion("Hay Pokémon en ciclos o sin raíz en los datos.")

    def _persistir(self):
        pokemon, evoluciones = [], []
        for arbol in self._familias:
            for nodo in arbol.nodos():
                registro = nodo.pokemon.obtener_datos()
                del registro["nivel_evolutivo"]
                pokemon.append(registro)
                if nodo.padre is not None:
                    evoluciones.append({"padre": nodo.padre.id, "hijo": nodo.id})
        pokemon.sort(key=lambda registro: registro["id"])
        evoluciones.sort(key=lambda relacion: (relacion["padre"], relacion["hijo"]))
        self._repositorio.guardar({"pokemon": pokemon, "evoluciones": evoluciones})

    # ----- Auxiliares --------------------------------------------------------

    def _registrar_familia(self, arbol):
        self._familias.append(arbol)
        for nodo in arbol.nodos():
            self._familia_por_id[nodo.id] = arbol

    def _familia_de(self, identificador):
        """Árbol que contiene el id. Lanza ErrorNoEncontrado si no existe."""
        arbol = self._familia_por_id.get(identificador)
        if arbol is None:
            raise ErrorNoEncontrado(f"No existe ningún Pokémon con el id {identificador}.")
        return arbol

    def _nodo_por_consulta(self, consulta):
        """Resuelve un id o un nombre a su nodo, para usarlo como raíz de un recorrido."""
        texto = str(consulta).strip()
        criterio = int(texto) if texto.isdigit() else texto
        resultado = self._buscador.buscar(self._raices(), criterio, "bfs")
        if resultado.encontrado is None:
            raise ErrorNoEncontrado(f"No existe ningún Pokémon llamado o con id '{texto}'.")
        return resultado.encontrado

    def _raices(self):
        return [arbol.raiz for arbol in sorted(self._familias, key=lambda arbol: arbol.raiz.id)]

    def _pokemon_ordenados(self):
        return [self._familia_por_id[identificador].obtener_nodo(identificador).pokemon
                for identificador in sorted(self._familia_por_id)]

    def _resumen(self, pokemon):
        return {
            "id": pokemon.id,
            "nombre": pokemon.nombre,
            "tipos": pokemon.tipos,
            "imagen": pokemon.imagen,
            "etapa": pokemon.nivel_evolutivo,
            "familia_id": self._familia_por_id[pokemon.id].raiz.id,
        }

    def _ficha(self, pokemon):
        datos = pokemon.obtener_datos()
        datos["familia_id"] = self._familia_por_id[pokemon.id].raiz.id
        return datos

    def _respuesta_busqueda(self, resultado, consulta):
        encontrado = resultado.encontrado
        return {
            "consulta": consulta,
            "algoritmo": resultado.algoritmo,
            "encontrado": encontrado is not None,
            "pokemon": self._resumen(encontrado.pokemon) if encontrado else None,
            "visitados": [self._resumen(nodo.pokemon) for nodo in resultado.orden],
            "total_visitados": len(resultado.orden),
            "mensaje": (
                f"Se encontró {encontrado.pokemon.nombre} con {resultado.algoritmo.upper()}."
                if encontrado
                else f"No se encontró ningún Pokémon con '{consulta}'."
            ),
        }

    def _respuesta_recorrido(self, resultado: ResultadoRecorrido, raiz=None):
        return {
            "algoritmo": resultado.algoritmo,
            "raiz": raiz,
            "orden": [self._resumen(nodo.pokemon) for nodo in resultado.orden],
            "total": len(resultado.orden),
        }

    @staticmethod
    def _validar_algoritmo(algoritmo):
        if algoritmo not in ALGORITMOS:
            raise ErrorValidacion("El algoritmo debe ser 'dfs' o 'bfs'.")
