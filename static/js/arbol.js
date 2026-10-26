/* ==========================================================================
   arbol.js · dibujo del árbol de evolución con D3.js
   Solo presenta datos: el árbol y los recorridos vienen del servidor.
   ========================================================================== */

(function () {
  "use strict";

  const RUTA_PLACEHOLDER = "/static/img/placeholder.svg";
  const RUTA_IMAGENES = "/static/img/";
  const RADIO_NODO = 50;
  const ESPACIO_HORIZONTAL = 190;
  const ESPACIO_VERTICAL = 170;
  const MARGEN = 60;
  const CLASES_ETAPA = {
    Inicial: "etapa-inicial",
    Intermedia: "etapa-intermedia",
    Final: "etapa-final",
    "Sin evoluciones": "etapa-sola",
  };

  const reducirMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function urlImagen(ruta) {
    return ruta ? RUTA_IMAGENES + ruta : RUTA_PLACEHOLDER;
  }

  function formatearId(id) {
    return "#" + String(id).padStart(3, "0");
  }

  /**
   * Crea una vista sobre un <svg>. Admite zoom, desplazamiento y selección por clic o teclado.
   * `onSeleccionar(id)` se llama cuando el usuario elige un nodo.
   */
  function crear(elementoSvg, opciones) {
    const svg = d3.select(elementoSvg);
    const capa = svg.append("g").attr("class", "capa-arbol");
    const zoom = d3.zoom()
      .scaleExtent([0.35, 2.5])
      .on("zoom", (evento) => capa.attr("transform", evento.transform));
    svg.call(zoom).on("dblclick.zoom", null);

    let jerarquiaActual = null;

    function render(datos, idSeleccionado) {
      capa.selectAll("*").remove();

      const jerarquia = d3.hierarchy(datos, (nodo) => nodo.hijos);
      d3.tree().nodeSize([ESPACIO_HORIZONTAL, ESPACIO_VERTICAL])(jerarquia);
      jerarquiaActual = jerarquia;

      capa.selectAll("path.enlace")
        .data(jerarquia.links())
        .join("path")
        .attr("class", "enlace")
        .attr("data-destino", (d) => d.target.data.id)
        .attr("d", d3.linkVertical().x((d) => d.x).y((d) => d.y));

      const nodos = capa.selectAll("g.nodo")
        .data(jerarquia.descendants(), (d) => d.data.id)
        .join(entrarNodo)
        .attr("transform", (d) => `translate(${d.x},${d.y})`);

      nodos.attr("class", (d) => `nodo ${CLASES_ETAPA[d.data.etapa] || "etapa-sola"}`);
      marcarSeleccion(idSeleccionado);
      ajustarVista(jerarquia);
    }

    function entrarNodo(entrada) {
      const grupo = entrada.append("g")
        .attr("tabindex", 0)
        .attr("role", "button")
        .attr("aria-label", (d) => `${d.data.nombre}, etapa ${d.data.etapa}`)
        .on("click", (evento, d) => opciones.onSeleccionar(d.data.id))
        .on("keydown", (evento, d) => {
          if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            opciones.onSeleccionar(d.data.id);
          }
        });

      grupo.append("circle")
        .attr("class", "fondo")
        .attr("r", RADIO_NODO + 6);

      grupo.append("image")
        .attr("x", -RADIO_NODO)
        .attr("y", -RADIO_NODO)
        .attr("width", RADIO_NODO * 2)
        .attr("height", RADIO_NODO * 2)
        .attr("href", (d) => cargarImagenConRespaldo(d.data.imagen))
        .attr("preserveAspectRatio", "xMidYMid meet");

      grupo.append("text")
        .attr("class", "id-nodo")
        .attr("y", -RADIO_NODO - 14)
        .text((d) => formatearId(d.data.id));

      grupo.append("text")
        .attr("class", "nombre-nodo")
        .attr("y", RADIO_NODO + 26)
        .text((d) => d.data.nombre);

      const insignia = grupo.append("g")
        .attr("class", "insignia")
        .attr("transform", `translate(${RADIO_NODO - 6},${-RADIO_NODO + 6})`)
        .attr("display", "none");
      insignia.append("circle").attr("r", 13);
      insignia.append("text");

      return grupo;
    }

    /**
     * Carga la imagen en memoria antes de asignarla. Si falla, se usa el respaldo
     * sin dejar una imagen rota en el diagrama.
     */
    function cargarImagenConRespaldo(ruta) {
      const origen = urlImagen(ruta);
      const prueba = new Image();
      prueba.onerror = () => {
        capa.selectAll("g.nodo image")
          .filter((d) => d && d.data && urlImagen(d.data.imagen) === origen)
          .attr("href", RUTA_PLACEHOLDER);
      };
      prueba.src = origen;
      return origen;
    }

    function marcarSeleccion(idSeleccionado) {
      capa.selectAll("g.nodo")
        .classed("seleccionado", (d) => d.data.id === idSeleccionado)
        .attr("aria-current", (d) => (d.data.id === idSeleccionado ? "true" : null));
    }

    /** Resalta el nodo elegido con un pequeño pulso, salvo que el usuario pida menos movimiento. */
    function seleccionar(idSeleccionado) {
      marcarSeleccion(idSeleccionado);
      if (reducirMovimiento) return;
      capa.selectAll("g.nodo.seleccionado circle.fondo")
        .transition().duration(180).attr("r", RADIO_NODO + 12)
        .transition().duration(260).attr("r", RADIO_NODO + 6);
    }

    /** Muestra el orden de visita (1, 2, 3…) sobre los nodos recorridos. */
    function mostrarOrden(ids) {
      const posicion = new Map(ids.map((id, indice) => [id, indice + 1]));
      capa.selectAll("g.nodo").each(function (d) {
        const grupo = d3.select(this);
        const numero = posicion.get(d.data.id);
        grupo.select("g.insignia").attr("display", numero ? null : "none");
        grupo.select("g.insignia text").text(numero || "");
      });
      capa.selectAll("path.enlace").classed("resaltado", (d) => posicion.has(d.target.data.id));
    }

    function ajustarVista(jerarquia) {
      const nodos = jerarquia.descendants();
      const minX = d3.min(nodos, (d) => d.x) - RADIO_NODO - MARGEN;
      const maxX = d3.max(nodos, (d) => d.x) + RADIO_NODO + MARGEN;
      const minY = d3.min(nodos, (d) => d.y) - RADIO_NODO - MARGEN;
      const maxY = d3.max(nodos, (d) => d.y) + RADIO_NODO + MARGEN + 20;
      const ancho = elementoSvg.clientWidth;
      const alto = elementoSvg.clientHeight;
      if (!ancho || !alto) return; // El lienzo está oculto: se ajustará al mostrarse.
      const escala = Math.min(1, ancho / (maxX - minX), alto / (maxY - minY));
      const centroX = (minX + maxX) / 2;
      const centroY = (minY + maxY) / 2;
      const transformacion = d3.zoomIdentity
        .translate(ancho / 2, alto / 2)
        .scale(escala)
        .translate(-centroX, -centroY);
      svg.call(zoom.transform, transformacion);
    }

    return {
      render,
      seleccionar,
      mostrarOrden,
      acercar: () => svg.transition().duration(reducirMovimiento ? 0 : 250).call(zoom.scaleBy, 1.25),
      alejar: () => svg.transition().duration(reducirMovimiento ? 0 : 250).call(zoom.scaleBy, 0.8),
      centrar: () => {
        if (jerarquiaActual) ajustarVista(jerarquiaActual);
      },
    };
  }

  window.ArbolVista = { crear, formatearId, urlImagen };
})();
