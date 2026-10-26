/* ==========================================================================
   app.js · lógica de las páginas: catálogo, búsqueda, explorador y administración.
   Toda la lógica de negocio vive en el servidor; aquí solo se pide y se muestra.
   ========================================================================== */

(function () {
  "use strict";

  const RUTA_IMAGEN = "/static/img/";
  const PLACEHOLDER = "/static/img/placeholder.svg";
  const ATRIBUTO_RESPALDO = `onerror="this.onerror=null;this.src='${PLACEHOLDER}'"`;
  const pagina = document.body.dataset.pagina;

  // ----- Utilidades ----------------------------------------------------------

  function esc(texto) {
    return String(texto ?? "").replace(/[&<>"']/g, (caracter) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[caracter]));
  }

  function urlImagen(ruta) {
    return ruta ? RUTA_IMAGEN + ruta : PLACEHOLDER;
  }

  function formatearId(id) {
    return "#" + String(id).padStart(3, "0");
  }

  function tiposHtml(tipos) {
    return tipos.map((tipo) => `<span class="tipo" data-tipo="${esc(tipo)}">${esc(tipo)}</span>`).join("");
  }

  function separarLista(texto) {
    return texto.split(",").map((elemento) => elemento.trim()).filter(Boolean);
  }

  /** Pide datos a la API y devuelve `datos` o lanza un Error con mensaje legible. */
  async function pedir(url, opciones = {}) {
    let respuesta;
    try {
      respuesta = await fetch(url, {
        ...opciones,
        headers: {
          Accept: "application/json",
          ...(opciones.body ? { "Content-Type": "application/json" } : {}),
        },
      });
    } catch (_) {
      throw new Error("No se pudo conectar con el servidor. Revisa que la aplicación siga en marcha.");
    }

    let cuerpo = null;
    try {
      cuerpo = await respuesta.json();
    } catch (_) {
      cuerpo = null;
    }

    if (!respuesta.ok || !cuerpo || !cuerpo.ok) {
      const mensaje = cuerpo?.error?.mensaje || `El servidor respondió con el código ${respuesta.status}.`;
      throw new Error(mensaje);
    }
    return cuerpo.datos;
  }

  function mostrarAviso(elemento, texto, tipo) {
    elemento.className = `aviso aviso-${tipo}`;
    elemento.textContent = texto;
    elemento.hidden = false;
  }

  function tarjetaPokemon(pokemon) {
    return `
      <a class="tarjeta" href="/explorar/${pokemon.id}">
        <span class="numero">${formatearId(pokemon.id)}</span>
        <img class="imagen" src="${urlImagen(pokemon.imagen)}" alt="${esc(pokemon.nombre)}" loading="lazy" ${ATRIBUTO_RESPALDO}>
        <span class="nombre">${esc(pokemon.nombre)}</span>
        <span class="tipos">${tiposHtml(pokemon.tipos)}</span>
      </a>`;
  }

  // ----- Inicio: estadísticas, filtros, catálogo y búsqueda -------------------

  function tarjetaEstadistica(valor, rotulo) {
    return `<div class="estadistica"><span class="valor">${esc(valor)}</span><span class="rotulo">${esc(rotulo)}</span></div>`;
  }

  async function cargarEstadisticas() {
    const contenedor = document.getElementById("estadisticas");
    contenedor.innerHTML = `<div class="estado estado-cargando">Cargando estadísticas…</div>`;
    try {
      const datos = await pedir("/api/estadisticas");
      const etapas = datos.etapas;
      contenedor.innerHTML = [
        tarjetaEstadistica(datos.total_pokemon, "Pokémon registrados"),
        tarjetaEstadistica(datos.total_relaciones, "Relaciones evolutivas"),
        tarjetaEstadistica(datos.total_familias, "Líneas evolutivas"),
        tarjetaEstadistica(datos.profundidad_maxima, "Niveles de profundidad"),
        `<div class="estadistica estadistica-ancha">
           <span class="rotulo">Por etapa evolutiva</span>
           <span class="etapas">
             <span class="punto punto-inicial"></span> Inicial ${etapas.Inicial}
             <span class="punto punto-intermedia"></span> Intermedia ${etapas.Intermedia}
             <span class="punto punto-final"></span> Final ${etapas.Final}
           </span>
         </div>`,
      ].join("");
    } catch (error) {
      contenedor.innerHTML = `<div class="estado estado-error">${esc(error.message)}</div>`;
    }
  }

  let tipoActivo = "";

  async function cargarFiltrosDeTipo() {
    const contenedor = document.getElementById("filtro-tipos");
    try {
      const tipos = await pedir("/api/tipos");
      contenedor.innerHTML = ["", ...tipos]
        .map((tipo) => `<button type="button" class="filtro" data-tipo="${esc(tipo)}" aria-pressed="${tipo === tipoActivo}">${tipo ? esc(tipo) : "Todos"}</button>`)
        .join("");
    } catch (error) {
      contenedor.innerHTML = `<span class="suave">${esc(error.message)}</span>`;
    }
    contenedor.addEventListener("click", (evento) => {
      const boton = evento.target.closest("button[data-tipo]");
      if (!boton) return;
      tipoActivo = boton.dataset.tipo;
      contenedor.querySelectorAll("button").forEach((otro) => {
        otro.setAttribute("aria-pressed", String(otro === boton));
      });
      cargarCatalogo();
    });
  }

  async function cargarCatalogo() {
    const estado = document.getElementById("estado-catalogo");
    const rejilla = document.getElementById("catalogo");
    estado.hidden = false;
    estado.className = "estado estado-cargando";
    estado.textContent = "Cargando Pokémon…";
    rejilla.innerHTML = "";

    try {
      const url = tipoActivo ? `/api/pokemon?tipo=${encodeURIComponent(tipoActivo)}` : "/api/pokemon";
      const pokemon = await pedir(url);
      if (pokemon.length === 0) {
        estado.className = "estado";
        estado.textContent = "No hay Pokémon de ese tipo todavía.";
        return;
      }
      estado.hidden = true;
      estado.textContent = "";
      rejilla.innerHTML = pokemon.map(tarjetaPokemon).join("");
    } catch (error) {
      estado.className = "estado estado-error";
      estado.textContent = error.message;
    }
  }

  function resultadoBusquedaHtml(datos) {
    const lista = `
      <p class="suave">Orden de visita en ${datos.algoritmo.toUpperCase()} (${datos.total_visitados} nodos revisados):</p>
      <ul class="visitados">
        ${datos.visitados.map((pokemon, indice) => `
          <li>
            <span class="indice">${indice + 1}</span>
            <span class="${datos.encontrado && pokemon.id === datos.pokemon.id ? "encontrado" : ""}">${esc(pokemon.nombre)}</span>
          </li>`).join("")}
      </ul>`;

    if (!datos.encontrado) {
      return `<div class="aviso aviso-error">${esc(datos.mensaje)}</div>${lista}`;
    }

    const pokemon = datos.pokemon;
    return `
      <a class="resultado-tarjeta" href="/explorar/${pokemon.id}">
        <img src="${urlImagen(pokemon.imagen)}" alt="${esc(pokemon.nombre)}" ${ATRIBUTO_RESPALDO}>
        <div>
          <h3>${esc(pokemon.nombre)} <span class="suave">${formatearId(pokemon.id)}</span></h3>
          <p class="suave">Etapa: ${esc(pokemon.etapa)}</p>
          <div class="tipos">${tiposHtml(pokemon.tipos)}</div>
        </div>
      </a>
      ${lista}`;
  }

  function iniciarBusqueda() {
    const formulario = document.getElementById("formulario-busqueda");
    const resultado = document.getElementById("resultado-busqueda");

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const consulta = document.getElementById("consulta").value.trim();
      const algoritmo = document.getElementById("algoritmo").value;

      if (!consulta) {
        resultado.innerHTML = `<div class="aviso aviso-error">Escribe un nombre o un identificador para buscar.</div>`;
        return;
      }

      resultado.innerHTML = `<div class="estado estado-cargando">Buscando con ${algoritmo.toUpperCase()}…</div>`;
      try {
        const datos = await pedir(`/api/buscar?q=${encodeURIComponent(consulta)}&algoritmo=${algoritmo}`);
        resultado.innerHTML = resultadoBusquedaHtml(datos);
      } catch (error) {
        resultado.innerHTML = `<div class="aviso aviso-error">${esc(error.message)}</div>`;
      }
    });
  }

  function iniciarInicio() {
    cargarEstadisticas();
    cargarFiltrosDeTipo();
    cargarCatalogo();
    iniciarBusqueda();
  }

  // ----- Explorador de árboles -----------------------------------------------

  function iniciarExplorador() {
    const contenedor = document.querySelector(".explorador");
    const lienzo = document.getElementById("lienzo-arbol");
    const mensajeArbol = document.getElementById("mensaje-arbol");
    const ficha = document.getElementById("ficha");
    const recorridos = document.getElementById("recorridos");
    const botonesAlgoritmo = document.querySelectorAll(".segmentado button[data-algoritmo]");

    const vista = window.ArbolVista.crear(document.querySelector("#svg-arbol"), {
      onSeleccionar: (id) => seleccionar(id, true),
    });

    let familiaDibujada = null;
    let familiaActual = null;
    let tieneEvoluciones = false;
    let algoritmoActivo = "dfs";
    let solicitudSeleccion = 0;
    let solicitudRecorrido = 0;

    function renderFicha(datos) {
      const pokemon = datos.pokemon;
      const padre = datos.padre
        ? `<li><a href="/explorar/${datos.padre.id}" data-seleccionar="${datos.padre.id}">${esc(datos.padre.nombre)}</a></li>`
        : "";
      const hijos = datos.hijos.length
        ? datos.hijos.map((hijo) => `<li><a href="/explorar/${hijo.id}" data-seleccionar="${hijo.id}">${esc(hijo.nombre)}</a></li>`).join("")
        : `<li><span>Ninguna: es la forma final</span></li>`;
      const ruta = datos.ruta
        .map((paso, indice) => `${indice ? '<span class="flecha">→</span>' : ""}<a href="/explorar/${paso.id}" data-seleccionar="${paso.id}">${esc(paso.nombre)}</a>`)
        .join("");
      const habilidades = pokemon.habilidades.length
        ? pokemon.habilidades.map((habilidad) => `<li><span>${esc(habilidad)}</span></li>`).join("")
        : `<li><span>Sin registrar</span></li>`;

      return `
        <div class="ficha-cabecera">
          <img class="ficha-imagen" src="${urlImagen(pokemon.imagen)}" alt="${esc(pokemon.nombre)}" ${ATRIBUTO_RESPALDO}>
          <h2>${esc(pokemon.nombre)}</h2>
          <span class="ficha-id">${formatearId(pokemon.id)} · Etapa ${esc(datos.etapa)}</span>
          <div class="ficha-tipos">${tiposHtml(pokemon.tipos)}</div>
        </div>
        <p class="ficha-descripcion">${esc(pokemon.descripcion) || "Sin descripción registrada."}</p>
        <div class="ficha-seccion"><h3>Habilidades</h3><ul>${habilidades}</ul></div>
        <div class="ficha-seccion"><h3>Preevolución</h3><ul>${padre || "<li><span>Ninguna: es la forma inicial</span></li>"}</ul></div>
        <div class="ficha-seccion"><h3>Evoluciones siguientes</h3><ul>${hijos}</ul></div>
        <div class="ficha-seccion"><h3>Ruta desde la raíz</h3><div class="ruta">${ruta}</div></div>`;
    }

    function mostrarSinEvoluciones(nombre) {
      lienzo.hidden = true;
      mensajeArbol.hidden = false;
      mensajeArbol.innerHTML = `
        <strong>${esc(nombre)} no tiene evoluciones registradas.</strong>
        <p class="suave">Sin líneas evolutivas no hay diagrama que dibujar.</p>`;
      familiaDibujada = null;
    }

    function dibujarArbol(datosArbol, idSeleccionado) {
      if (!datosArbol.tiene_evoluciones) {
        mostrarSinEvoluciones(datosArbol.arbol.nombre);
        return;
      }
      // Hay que mostrar el lienzo antes de dibujar: D3 necesita su tamaño para encuadrar.
      lienzo.hidden = false;
      mensajeArbol.hidden = true;
      if (familiaDibujada !== datosArbol.raiz_id) {
        vista.render(datosArbol.arbol, idSeleccionado);
        familiaDibujada = datosArbol.raiz_id;
      } else {
        vista.seleccionar(idSeleccionado);
      }
    }

    async function seleccionar(id, actualizarUrl) {
      const solicitud = ++solicitudSeleccion;
      if (actualizarUrl) {
        history.pushState({ id }, "", `/explorar/${id}`);
      }
      ficha.innerHTML = `<div class="estado estado-cargando">Cargando ficha…</div>`;

      try {
        const [datosFicha, datosArbol] = await Promise.all([
          pedir(`/api/pokemon/${id}`),
          pedir(`/api/pokemon/${id}/evoluciones`),
        ]);
        if (solicitud !== solicitudSeleccion) return;

        tieneEvoluciones = datosArbol.tiene_evoluciones;
        familiaActual = datosArbol.raiz_id;
        dibujarArbol(datosArbol, id);
        ficha.innerHTML = renderFicha(datosFicha);
        document.title = `${datosFicha.pokemon.nombre} · PokéDex Explorer`;
        await cargarRecorridos(algoritmoActivo);
      } catch (error) {
        if (solicitud !== solicitudSeleccion) return;
        ficha.innerHTML = `<div class="estado-ficha estado-error">${esc(error.message)}</div>`;
        lienzo.hidden = true;
        mensajeArbol.hidden = false;
        mensajeArbol.className = "estado estado-error mensaje-vacio";
        mensajeArbol.textContent = error.message;
        recorridos.innerHTML = "";
      }
    }

    function renderOrden(datos) {
      const explicacion = datos.algoritmo === "dfs"
        ? "DFS baja por cada rama hasta el final antes de pasar a la siguiente."
        : "BFS visita todos los Pokémon de un nivel antes de bajar al siguiente.";
      return `
        <p class="suave">${esc(explicacion)}</p>
        <ul class="visitados">
          ${datos.orden.map((pokemon, indice) => `
            <li><span class="indice">${indice + 1}</span>${esc(pokemon.nombre)}</li>`).join("")}
        </ul>`;
    }

    function columnaComparacion(titulo, descripcion, datos) {
      return `
        <div>
          <h3>${esc(titulo)}</h3>
          <p class="suave">${esc(descripcion)}</p>
          <ul class="visitados">
            ${datos.orden.map((pokemon, indice) => `
              <li><span class="indice">${indice + 1}</span>${esc(pokemon.nombre)}</li>`).join("")}
          </ul>
        </div>`;
    }

    function renderComparacion(datos) {
      const nota = datos.mismo_orden
        ? "Ambos recorridos visitan los Pokémon en el mismo orden."
        : "El orden difiere: DFS completa una rama antes de volver; BFS recorre por niveles.";
      return `
        <div class="comparacion">
          ${columnaComparacion("DFS · profundidad", "Baja por cada rama.", datos.dfs)}
          ${columnaComparacion("BFS · anchura", "Recorre por niveles con una cola.", datos.bfs)}
        </div>
        <p class="nota-comparacion ${datos.mismo_orden ? "igual" : "distinto"}">${nota}</p>`;
    }

    async function cargarRecorridos(algoritmo) {
      const solicitud = ++solicitudRecorrido;
      algoritmoActivo = algoritmo;
      botonesAlgoritmo.forEach((boton) => {
        boton.setAttribute("aria-pressed", String(boton.dataset.algoritmo === algoritmo));
      });

      if (!tieneEvoluciones) {
        recorridos.innerHTML = `<div class="estado">Sin recorridos: este Pokémon no tiene línea evolutiva.</div>`;
        vista.mostrarOrden([]);
        return;
      }

      recorridos.innerHTML = `<div class="estado estado-cargando">Calculando recorrido…</div>`;
      try {
        if (algoritmo === "comparar") {
          const comparacion = await pedir(`/api/recorrido?algoritmo=comparar&raiz=${familiaActual}`);
          if (solicitud !== solicitudRecorrido) return;
          recorridos.innerHTML = renderComparacion(comparacion);
          vista.mostrarOrden([]);
        } else {
          const datos = await pedir(`/api/recorrido?algoritmo=${algoritmo}&raiz=${familiaActual}`);
          if (solicitud !== solicitudRecorrido) return;
          recorridos.innerHTML = renderOrden(datos);
          vista.mostrarOrden(datos.orden.map((pokemon) => pokemon.id));
        }
      } catch (error) {
        if (solicitud !== solicitudRecorrido) return;
        recorridos.innerHTML = `<div class="aviso aviso-error">${esc(error.message)}</div>`;
      }
    }

    // Clic en un enlace de la ficha (padre, hijos o ruta): selecciona sin recargar la página.
    ficha.addEventListener("click", (evento) => {
      const enlace = evento.target.closest("[data-seleccionar]");
      if (!enlace) return;
      evento.preventDefault();
      seleccionar(Number(enlace.dataset.seleccionar), true);
    });

    document.querySelector(".segmentado").addEventListener("click", (evento) => {
      const boton = evento.target.closest("button[data-algoritmo]");
      if (boton) cargarRecorridos(boton.dataset.algoritmo);
    });

    document.getElementById("zoom-mas").addEventListener("click", () => vista.acercar());
    document.getElementById("zoom-menos").addEventListener("click", () => vista.alejar());
    document.getElementById("zoom-centrar").addEventListener("click", () => vista.centrar());

    window.addEventListener("popstate", () => {
      const coincidencia = window.location.pathname.match(/^\/explorar\/(\d+)$/);
      if (coincidencia) seleccionar(Number(coincidencia[1]), false);
    });

    seleccionar(Number(contenedor.dataset.pokemonId), false);
  }

  // ----- Administración --------------------------------------------------------

  function iniciarAdministracion() {
    const tipos = (window.POKEDEX && window.POKEDEX.tipos) || [];
    const opcionesTipo = (conVacio) =>
      (conVacio ? '<option value="">Ninguno</option>' : "") +
      tipos.map((tipo) => `<option value="${esc(tipo)}">${esc(tipo)}</option>`).join("");

    document.getElementById("registro-tipo1").innerHTML = opcionesTipo(false);
    document.getElementById("registro-tipo2").innerHTML = opcionesTipo(true);
    document.getElementById("edicion-tipo1").innerHTML = opcionesTipo(false);
    document.getElementById("edicion-tipo2").innerHTML = opcionesTipo(true);

    const avisoRegistro = document.getElementById("aviso-registro");
    const avisoEvolucion = document.getElementById("aviso-evolucion");
    const avisoEdicion = document.getElementById("aviso-edicion");
    const selectPadre = document.getElementById("evolucion-padre");
    const selectHijo = document.getElementById("evolucion-hijo");
    const selectEdicion = document.getElementById("edicion-pokemon");
    const formularioEdicion = document.getElementById("formulario-edicion");

    /** Rellena los selectores con el catálogo, conservando la selección si sigue existiendo. */
    async function recargarCatalogo() {
      const catalogo = await pedir("/api/pokemon");
      const todos = catalogo.map((pokemon) => `<option value="${pokemon.id}">${formatearId(pokemon.id)} · ${esc(pokemon.nombre)}</option>`).join("");
      const sinEvoluciones = catalogo
        .filter((pokemon) => pokemon.etapa === "Sin evoluciones")
        .map((pokemon) => `<option value="${pokemon.id}">${formatearId(pokemon.id)} · ${esc(pokemon.nombre)}</option>`)
        .join("");

      const previoPadre = selectPadre.value;
      const previoHijo = selectHijo.value;
      const previoEdicion = selectEdicion.value;

      selectPadre.innerHTML = todos;
      selectHijo.innerHTML = sinEvoluciones || '<option value="">No hay Pokémon sin evoluciones</option>';
      selectEdicion.innerHTML = todos;

      if (previoPadre) selectPadre.value = previoPadre;
      if (previoHijo) selectHijo.value = previoHijo;
      if (previoEdicion) selectEdicion.value = previoEdicion;
      await cargarFormularioEdicion(selectEdicion.value);
    }

    async function cargarFormularioEdicion(id) {
      if (!id) return;
      try {
        const { pokemon } = await pedir(`/api/pokemon/${id}`);
        formularioEdicion.elements.namedItem("nombre").value = pokemon.nombre;
        formularioEdicion.elements.namedItem("tipo1").value = pokemon.tipos[0] || "";
        formularioEdicion.elements.namedItem("tipo2").value = pokemon.tipos[1] || "";
        formularioEdicion.elements.namedItem("habilidades").value = pokemon.habilidades.join(", ");
        formularioEdicion.elements.namedItem("descripcion").value = pokemon.descripcion;
        formularioEdicion.elements.namedItem("imagen").value = pokemon.imagen;
        avisoEdicion.hidden = true;
      } catch (error) {
        mostrarAviso(avisoEdicion, error.message, "error");
      }
    }

    selectEdicion.addEventListener("change", () => cargarFormularioEdicion(selectEdicion.value));

    document.getElementById("formulario-registro").addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const formulario = evento.target;
      const datos = new FormData(formulario);
      const idTexto = String(datos.get("id")).trim();
      const cuerpo = {
        id: idTexto ? Number(idTexto) : null,
        nombre: String(datos.get("nombre")).trim(),
        tipos: [datos.get("tipo1"), datos.get("tipo2")].filter(Boolean),
        habilidades: separarLista(String(datos.get("habilidades"))),
        descripcion: String(datos.get("descripcion")).trim(),
        imagen: String(datos.get("imagen")).trim(),
      };
      try {
        const nuevo = await pedir("/api/pokemon", { method: "POST", body: JSON.stringify(cuerpo) });
        mostrarAviso(avisoRegistro, `${nuevo.nombre} se registró con el id ${nuevo.id}.`, "exito");
        formulario.reset();
        await recargarCatalogo();
      } catch (error) {
        mostrarAviso(avisoRegistro, error.message, "error");
      }
    });

    document.getElementById("formulario-evolucion").addEventListener("submit", async (evento) => {
      evento.preventDefault();
      if (!selectPadre.value || !selectHijo.value) {
        mostrarAviso(avisoEvolucion, "Elige el Pokémon padre y una nueva forma sin evoluciones previas.", "error");
        return;
      }
      const cuerpo = {
        padre_id: Number(selectPadre.value),
        hijo_id: Number(selectHijo.value),
      };
      try {
        const relacion = await pedir("/api/evoluciones", { method: "POST", body: JSON.stringify(cuerpo) });
        mostrarAviso(avisoEvolucion, `${relacion.hijo.nombre} ahora evoluciona desde ${relacion.padre.nombre}.`, "exito");
        await recargarCatalogo();
      } catch (error) {
        mostrarAviso(avisoEvolucion, error.message, "error");
      }
    });

    formularioEdicion.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      if (!selectEdicion.value) {
        mostrarAviso(avisoEdicion, "Elige un Pokémon para editar.", "error");
        return;
      }
      const datos = new FormData(formularioEdicion);
      const cuerpo = {
        nombre: String(datos.get("nombre")).trim(),
        tipos: [datos.get("tipo1"), datos.get("tipo2")].filter(Boolean),
        habilidades: separarLista(String(datos.get("habilidades"))),
        descripcion: String(datos.get("descripcion")).trim(),
        imagen: String(datos.get("imagen")).trim(),
      };
      try {
        const actualizado = await pedir(`/api/pokemon/${selectEdicion.value}`, {
          method: "PUT",
          body: JSON.stringify(cuerpo),
        });
        mostrarAviso(avisoEdicion, `Cambios guardados en ${actualizado.nombre}.`, "exito");
        await recargarCatalogo();
      } catch (error) {
        mostrarAviso(avisoEdicion, error.message, "error");
      }
    });

    recargarCatalogo().catch((error) => mostrarAviso(avisoRegistro, error.message, "error"));
  }

  // ----- Arranque --------------------------------------------------------------

  if (pagina === "inicio") iniciarInicio();
  if (pagina === "explorar") iniciarExplorador();
  if (pagina === "admin") iniciarAdministracion();
})();
