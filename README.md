# PokéDex Explorer

Aplicación web para explorar las líneas evolutivas de los Pokémon. Cada línea evolutiva es un **árbol**: la forma inicial es la raíz, las evoluciones son sus descendientes y las ramificaciones (como las de Eevee) son hijos de un mismo padre.

- **Backend:** Python 3 + Flask, con clases independientes para el modelo, los algoritmos y la persistencia.
- **Frontend:** HTML5, CSS3 y JavaScript, con D3.js para dibujar el árbol.
- **Datos:** JSON local (`data/pokemon.json`). No necesita conexión a internet. Las imágenes oficiales se incluyen en el proyecto.

---

## Requisitos

- Python 3.10 o superior (probado con Python 3.14).
- Un navegador moderno.

---

## Instalación y ejecución en Windows

Abre **PowerShell** (o el *Símbolo del sistema*) dentro de la carpeta `PokeDexExplorer`.

1. Crear el entorno virtual:

   ```bash
   py -m venv .venv
   ```

2. Activarlo.

   En PowerShell:

   ```bash
   .venv\Scripts\Activate.ps1
   ```

   Si PowerShell bloquea el script, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repite el paso.

   En el Símbolo del sistema (CMD):

   ```bash
   .venv\Scripts\activate.bat
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecutar la aplicación:

   ```bash
   python app.py
   ```

5. Abrir el navegador en **http://127.0.0.1:5000**.

Para detener el servidor, presiona `Ctrl + C`.

### Ejecutar las pruebas

Con el entorno virtual activado:

```bash
python -m unittest discover -s tests -v
```

Las pruebas usan una copia temporal de `data/pokemon.json`, así que no modifican tus datos.

---

## Estructura del proyecto

```
PokeDexExplorer/
├── app.py                       # Punto de entrada y fábrica de la aplicación Flask
├── requirements.txt
├── README.md
├── models/                      # Modelo de dominio
│   ├── errores.py               # Errores de negocio con código HTTP
│   ├── pokemon.py               # Clase Pokemon (datos y validaciones)
│   ├── nodo.py                  # Clase Nodo (padre, hijos, etapa)
│   └── arbol_evolucion.py       # Clase ArbolEvolucion (inserción, validaciones, consultas)
├── services/                    # Reglas de negocio y algoritmos
│   ├── buscador.py              # Clase Buscador (DFS, BFS, búsqueda y comparación)
│   └── pokemon_service.py       # Clase PokemonService (orquesta modelos y persistencia)
├── repositories/
│   └── pokemon_repository.py    # Lectura y escritura atómica de data/pokemon.json
├── web/                         # Capa HTTP
│   ├── rutas_api.py             # Endpoints REST (/api/...)
│   ├── rutas_vistas.py          # Páginas HTML
│   └── respuestas.py            # Formato común de respuestas JSON
├── data/
│   └── pokemon.json             # Datos de ejemplo y relaciones evolutivas
├── templates/                   # index.html, detalle.html, admin.html, base.html
├── static/
│   ├── css/styles.css
│   ├── js/app.js                # Lógica de cada página
│   ├── js/arbol.js              # Dibujo del árbol con D3 (zoom, selección, orden)
│   ├── js/vendor/d3.min.js      # D3.js v7.9.0 incluido localmente
│   └── img/                     # Imágenes oficiales y placeholder.svg (respaldo)
└── tests/                       # Pruebas unitarias y de integración
    ├── test_arbol.py
    ├── test_buscador.py
    ├── test_pokemon_service.py
    ├── test_api.py
    └── utilidades.py
```

Cada clase tiene una responsabilidad:

| Clase | Responsabilidad |
| --- | --- |
| `Pokemon` | Datos de un Pokémon, validación de sus campos y actualización controlada. |
| `Nodo` | Un elemento del árbol: referencia a su padre, lista de hijos y cálculo de su etapa. |
| `ArbolEvolucion` | Una familia completa: raíz, inserción de evoluciones, validación de duplicados, autoenlaces y ciclos, rutas y descendientes. |
| `Buscador` | Implementa DFS y BFS, la búsqueda y la comparación de recorridos. |
| `PokemonService` | Orquesta el catálogo: consultas, altas, ediciones, evoluciones y persistencia. Las rutas de Flask solo llaman a esta clase. |
| `PokemonRepository` | Lee y escribe el JSON. Escribe en un archivo temporal y luego lo reemplaza, para no dejar datos a medias. |

---

## Estructura de datos: árboles de evolución

El catálogo se modela como un **bosque**: cada familia es un `ArbolEvolucion` distinto. Hay cuatro familias de ejemplo:

| Raíz | Descendientes |
| --- | --- |
| Bulbasaur (1) | Ivysaur (2) → Venusaur (3) |
| Charmander (4) | Charmeleon (5) → Charizard (6) |
| Squirtle (7) | Wartortle (8) → Blastoise (9) |
| Eevee (133) | Vaporeon (134), Jolteon (135), Flareon (136), Espeon (196), Umbreon (197) |

Reglas del modelo:

- **Un único padre por nodo.** Un Pokémon tiene como máximo una preevolución. Esto convierte la estructura en un árbol y no en un grafo.
- **Una sola raíz por árbol.** La raíz es la forma inicial de la línea.
- **Etapas calculadas por posición:**
  - Raíz con hijos → **Inicial**.
  - Nodo con padre e hijos → **Intermedia**.
  - Hoja con padre → **Final**.
  - Raíz sin hijos → **Sin evoluciones**.

  La etapa no se escribe a mano: `ArbolEvolucion` la recalcula cuando cambia la estructura.

---

## API REST

Todas las respuestas usan el mismo formato:

```json
{ "ok": true,  "datos": { ... } }
{ "ok": false, "error": { "codigo": "validacion", "mensaje": "..." } }
```

| Método | Ruta | Descripción | Códigos |
| --- | --- | --- | --- |
| GET | `/api/pokemon` | Catálogo. Admite `?tipo=Fuego`. | 200, 400 |
| POST | `/api/pokemon` | Registra un Pokémon sin evoluciones. | 201, 400, 409 |
| GET | `/api/pokemon/<id>` | Ficha: datos, padre, hijos, ruta, etapa. | 200, 404 |
| PUT | `/api/pokemon/<id>` | Edita nombre, tipos, descripción, habilidades o imagen. | 200, 400, 404 |
| GET | `/api/pokemon/<id>/evoluciones` | Árbol anidado de la familia para dibujarlo. | 200, 404 |
| POST | `/api/evoluciones` | Crea una relación `{"padre_id": 1, "hijo_id": 2}`. | 201, 400, 404, 409 |
| GET | `/api/buscar?q=...&algoritmo=dfs\|bfs` | Busca por nombre o id con DFS o BFS. Devuelve el orden de visita. | 200, 400 |
| GET | `/api/recorrido?algoritmo=dfs\|bfs\|comparar&raiz=...` | Recorrido completo del catálogo o de la familia/subárbol de `raiz`. | 200, 400, 404 |
| GET | `/api/tipos` | Tipos presentes en el catálogo. | 200 |
| GET | `/api/estadisticas` | Totales, familias, profundidad y etapas. | 200 |

Páginas: `/` (catálogo, búsqueda y estadísticas), `/explorar/<id>` (diagrama y ficha), `/admin` (registro, evoluciones y edición).

---

## Validaciones

- **Identificadores duplicados:** se rechazan con `409`.
- **Autoenlaces:** un Pokémon no puede evolucionar en sí mismo (`409`).
- **Ciclos:** `ArbolEvolucion.conectar` comprueba que el nuevo nodo no sea ancestro del padre. Además, la carga de datos rechaza ciclos en el JSON.
- **Relaciones incompatibles:**
  - Un Pokémon con preevolución no puede volver a enlazarse.
  - Un Pokémon que ya tiene evoluciones no puede convertirse en evolución de otro, porque eso fusionaría familias.
  - Un padre o hijo inexistente devuelve `404`.
- **Datos inválidos:** tipos desconocidos, más de dos tipos, nombres fuera de rango o JSON mal formado devuelven `400` con un mensaje en español.
- **Errores internos:** la API nunca muestra trazas. Se registran en el servidor y el cliente recibe un mensaje genérico con código `500`.

---

## Algoritmos y complejidad

Sea `N` el número de nodos, `H` la altura del árbol y `A` su ancho máximo.

| Operación | Implementación | Tiempo | Espacio |
| --- | --- | --- | --- |
| Inserción (`conectar`) | Búsqueda del padre por índice `dict` y comprobación de ciclo por ancestros. | O(H) | O(1) adicional |
| Buscar nodo por id | Índice `dict` `id → nodo`. | O(1) | O(N) en el índice |
| DFS (`Buscador.dfs`) | Preorden con pila explícita. | O(N) | O(H) |
| BFS (`Buscador.bfs`) | Recorrido por niveles con `collections.deque`. | O(N) | O(A) |
| Búsqueda por nombre o id | DFS o BFS, deteniéndose al encontrar el primer resultado. | O(N) en el peor caso | O(H) o O(A) |
| Descendientes | Pila explícita en preorden sobre el subárbol. | O(D) donde D son los descendientes | O(H) |
| Ruta desde la raíz | Subir por los padres y luego invertir la lista. | O(H) | O(H) |
| Validación de ciclos | Recorrer los ancestros del padre. | O(H) | O(1) |
| Actualizar etapas | Solo cambian el padre y el nuevo nodo. | O(1) | O(1) |

Notas:

- Los recorridos usan pilas o colas explícitas, así que no dependen del límite de recursión de Python.
- La búsqueda se detiene en cuanto encuentra el Pokémon. El orden de visita devuelto muestra exactamente qué nodos se revisaron.
- DFS y BFS siempre visitan el mismo conjunto de nodos; lo que cambia es el orden. El orden solo difiere cuando hay ramas con más de un nivel. En la familia de Eevee coinciden, porque todos sus descendientes están a un solo nivel de la raíz.

---

## Ejemplos de ejecución

Los siguientes resultados salen de ejecutar el código del proyecto.

### Inserción en el árbol de Eevee

```python
from models.arbol_evolucion import ArbolEvolucion
from models.pokemon import Pokemon

arbol = ArbolEvolucion()
arbol.establecer_raiz(Pokemon(133, "Eevee", ["Normal"]))
arbol.conectar(133, Pokemon(134, "Vaporeon", ["Agua"]))
arbol.conectar(133, Pokemon(196, "Espeon", ["Psíquico"]))
```

Si se intenta insertar de nuevo el id 134, el árbol lanza `ErrorConflicto: El Pokémon 134 ya existe en este árbol.`

### Recorrido del árbol completo

```python
from services.buscador import Buscador

b = Buscador()
[n.pokemon.nombre for n in b.dfs(arbol.raiz).orden]   # ['Eevee', 'Vaporeon', 'Espeon']
[n.pokemon.nombre for n in b.bfs(arbol.raiz).orden]   # ['Eevee', 'Vaporeon', 'Espeon']
```

### Búsqueda DFS y BFS

Con la línea de Charmander cargada desde `data/pokemon.json`:

```python
from services.pokemon_service import PokemonService

servicio = PokemonService()
servicio.buscar("Charizard", "dfs")["visitados"]
# Bulbasaur, Ivysaur, Venusaur, Charmander, Charmeleon, Charizard
# (la búsqueda recorre las familias en orden de id de raíz y se detiene al encontrar el Pokémon)

servicio.recorrido("comparar", raiz="Charmander")["mismo_orden"]   # True: la línea no tiene ramas
```

Dentro de la familia de Eevee, `buscar("Espeon", "dfs")` recorre Eevee, Vaporeon, Jolteon, Flareon y Espeon, y se detiene al encontrarlo. Como las familias se revisan antes, el listado completo de visitados incluye también las líneas de Bulbasaur, Charmander y Squirtle.

### Ruta y descendientes

```python
[p.nombre for p in arbol.ruta_desde_raiz(196)]   # ['Eevee', 'Espeon']
[n.pokemon.nombre for n in arbol.descendientes(133)]   # ['Vaporeon', 'Espeon']
```

### Peticiones HTTP de ejemplo

```bash
curl "http://127.0.0.1:5000/api/buscar?q=Umbreon&algoritmo=bfs"
curl "http://127.0.0.1:5000/api/recorrido?algoritmo=comparar&raiz=Eevee"
```

En Windows PowerShell, usa `curl.exe` o `Invoke-RestMethod`.

---

## Datos y créditos

- `data/pokemon.json` contiene 15 Pokémon de ejemplo: tres líneas iniciales y la familia de Eevee. Los nombres, números y tipos corresponden a la Pokédex nacional. Las descripciones y habilidades son textos didácticos y conviene revisarlos antes de una presentación.
- Las imágenes de `static/img/pokemon/` son las *official artwork* de [PokéAPI](https://pokeapi.co/), que las distribuye para uso educativo. Los Pokémon y sus nombres son marcas de Nintendo, Game Freak y The Pokémon Company.
- D3.js v7.9.0 está incluido en `static/js/vendor/` y se usa bajo licencia ISC.

---

## Limitaciones conocidas

- No se pueden borrar Pokémon ni deshacer relaciones evolutivas. El enunciado no lo pedía.
- No se pueden fusionar dos familias ya existentes; el hijo de una nueva relación debe ser un Pokémon sin evoluciones.
- La aplicación no tiene autenticación: está pensada para uso local o demostración.
- Las pruebas y la ejecución se han verificado en macOS. Las instrucciones de Windows siguen el mismo procedimiento estándar de Python, pero conviene comprobarlas en la máquina de la demostración.
