// Marcar navegación activa
document.addEventListener('DOMContentLoaded', () => {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (currentPath === href || (currentPath === '/' && href === '/')) {
      link.classList.add('active');
    }
  });
});

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

function formatARS(n) {
  try {
    return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" }).format(n);
  } catch {
    return `$ ${n}`;
  }
}

async function initDashboard() {
  const box = document.getElementById("live-data");
  if (!box) return;

  try {
    const data = await fetchJSON("/api/dashboard");
    box.textContent = pretty(data);

    const resumen = data.resumen_cuenta || {};
    const saldo = resumen.saldo_total ?? 0;
    const movMes = resumen.movimientos_mes ?? 0;
    const cats = resumen.categorias_activas ?? 0;
    const estado = data.mensaje || "OK";

    const elSaldo = document.getElementById("kpi-saldo");
    const elMov = document.getElementById("kpi-movimientos");
    const elCats = document.getElementById("kpi-categorias");
    const elEstado = document.getElementById("kpi-estado");

    if (elSaldo) elSaldo.textContent = formatARS(saldo);
    if (elMov) elMov.textContent = String(movMes);
    if (elCats) elCats.textContent = String(cats);
    if (elEstado) elEstado.textContent = estado;

    const list = document.getElementById("ultimos-movs");
    if (list) {
      list.innerHTML = "";
      const items = data.ultimos_movimientos || [];
      for (const m of items) {
        const row = document.createElement("div");
        row.className = "mov-row";
        const fecha = m.fecha || "";
        const desc = m.descripcion || "";
        const cat = m.categoria || "";
        const monto = m.monto ?? 0;
        const movId = m.id;

        row.innerHTML = `
          <div class="mov-content">
            <div class="mov-main"><strong>${fecha}</strong> — ${desc}</div>
            <div class="mov-sub">${cat} · ${formatARS(monto)}</div>
          </div>
          <div class="mov-actions">
            <button class="btn-icon btn-edit" onclick="editarMovimiento(${movId})" title="Editar">✏️</button>
            <button class="btn-icon btn-delete" onclick="eliminarMovimiento(${movId})" title="Eliminar">🗑️</button>
          </div>
        `;
        list.appendChild(row);
      }
    }
  } catch (err) {
    box.textContent = `Error cargando /api/dashboard:\n${err}`;
  }
}

async function initProcesoCompleto() {
  const form = document.getElementById("upload-form");
  if (!form) return;

  const input = document.getElementById("excel-file");
  const btn = document.getElementById("process-btn");
  const status = document.getElementById("upload-status");
  const out = document.getElementById("process-result");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!input || !input.files || input.files.length === 0) {
      if (status) status.textContent = "Elegí un archivo Excel primero.";
      return;
    }

    const file = input.files[0];
    const fd = new FormData();
    fd.append("archivo", file);

    try {
      if (btn) btn.disabled = true;
      if (status) status.textContent = "Procesando… (esto puede tardar unos segundos)";
      if (out) out.textContent = "";

      const res = await fetch("/api/proceso-completo", {
        method: "POST",
        body: fd,
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const msg = data?.detail ? JSON.stringify(data.detail) : `${res.status} ${res.statusText}`;
        throw new Error(msg);
      }

      if (status) status.textContent = "OK ✅ Procesado completo. Aplicando reglas automáticamente…";
      if (out) out.textContent = pretty(data);

      // AUTO-APLICAR REGLAS al batch recién cargado
      try {
        const batchId = data?.batch_id || data?.consolidar?.batch_id;

        if (batchId) {
          // Aplicar reglas solo a movimientos sin categoría del batch nuevo
          const applyRes = await fetch("/api/reglas/aplicar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              batch_id: batchId,
              solo_sin_categoria: true
            })
          });

          const applyData = await applyRes.json().catch(() => ({}));

          if (applyRes.ok) {
            const actualizados = applyData?.actualizados || 0;
            if (status) status.textContent = `OK ✅ Batch cargado y reglas aplicadas (${actualizados} movimientos categorizados). Actualizando dashboard…`;
          } else {
            // Si falla aplicar reglas, NO bloquear - solo warning
            console.warn("Auto-aplicar reglas falló:", applyData);
            if (status) status.textContent = "OK ✅ Batch cargado correctamente. Las reglas no se aplicaron automáticamente (podés hacerlo manualmente). Actualizando dashboard…";
          }
        }
      } catch (applyErr) {
        // Si falla aplicar reglas, NO bloquear - solo warning
        console.warn("Auto-aplicar reglas error:", applyErr);
        if (status) status.textContent = "OK ✅ Batch cargado correctamente. Las reglas no se aplicaron automáticamente (podés hacerlo manualmente). Actualizando dashboard…";
      }

      await initDashboard(); // refresca KPIs + lista + debug

      // Disparar evento para refrescar selector de periodos
      window.dispatchEvent(new CustomEvent('refreshPeriodos'));
    } catch (err) {
      if (status) status.textContent = `Error ❌ ${err}`;
      if (out) out.textContent = String(err);
    } finally {
      if (btn) btn.disabled = false;
    }
  });
}

// ============================================
// FUNCIONES DE EDICIÓN (ETAPA 3)
// ============================================

let movimientoEditando = null;

// Definición de categorías y subcategorías
// v2.1 - 2025-12-19 - SAFE MODE: Nuevas opciones agregadas sin eliminar existentes
const CATEGORIAS = {
  "INGRESOS": {
    // Existentes (backward compatible)
    "Afiliados_DEBIN": "Afiliados DEBIN",
    "Pacientes_Transferencia": "Pacientes Transferencia",
    "Otros_Ingresos": "Otros Ingresos",
    // Nuevas (2025-12-19)
    "Ingresos - Transferencias": "Transferencias",
    "Ingresos - Transferencias Operativas": "Transferencias Operativas",
    "Ingresos - DEBIN Afiliados": "DEBIN Afiliados",
    "Ingresos - DEBIN Clientes": "DEBIN Clientes",
    "Ingresos - Tarjetas": "Tarjetas",
    "Ingresos - Ajustes / Devoluciones": "Ajustes / Devoluciones"
  },
  "EGRESOS": {
    // Existentes (backward compatible)
    "Prestadores_Farmacias": "Prestadores Farmacias",
    "Prestadores_Sanatorios": "Prestadores Sanatorios",
    "Prestadores_Profesionales": "Prestadores Profesionales",
    "Sueldos": "Sueldos",
    "Impuestos": "Impuestos",
    "Comisiones_Bancarias": "Comisiones Bancarias",
    "Servicios": "Servicios",
    "Gastos_Operativos": "Gastos Operativos",
    // Nuevas (2025-12-19)
    "Egresos - Transferencias": "Transferencias",
    "Egresos - Transferencias a Terceros": "Transferencias a Terceros",
    "Egresos - DEBIN Pagos": "DEBIN Pagos",
    "Egresos - Ajustes": "Ajustes"
  },
  "IMPUESTOS": {
    // Nuevas (2025-12-19)
    "Impuestos - Débitos y Créditos": "Débitos y Créditos",
    "Impuestos - IVA": "IVA",
    "Impuestos - IIBB": "IIBB",
    "Impuestos - AFIP": "AFIP",
    "Impuestos - Percepciones": "Percepciones",
    "Impuestos - Devoluciones": "Devoluciones"
  },
  "GASTOS_OPERATIVOS": {
    // Nuevas (2025-12-19)
    "Gastos Operativos - Compras": "Compras",
    "Gastos Operativos - Viáticos": "Viáticos",
    "Gastos Operativos - Compras Marketplace": "Compras Marketplace",
    "Gastos Operativos - Compras Operativas": "Compras Operativas",
    "Gastos Operativos - Insumos": "Insumos"
  },
  "COMISIONES_BANCARIAS": {
    // Nuevas (2025-12-19)
    "Comisiones Bancarias - Transferencias": "Transferencias",
    "Comisiones Bancarias - Cheques": "Cheques",
    "Comisiones Bancarias - Mantenimiento": "Mantenimiento",
    "Comisiones Bancarias - Otras": "Otras"
  },
  "PRESTADORES": {
    // Nuevas (2025-12-19)
    "Prestadores - Servicios": "Servicios",
    "Prestadores - Profesionales": "Profesionales",
    "Prestadores - Servicios Recurrentes": "Servicios Recurrentes",
    "Prestadores - Pagos Eventuales": "Pagos Eventuales"
  },
  "SERVICIOS": {
    // Nuevas (2025-12-19)
    "Servicios - Varios": "Varios",
    "Servicios - Electricidad": "Electricidad",
    "Servicios - Internet": "Internet",
    "Servicios - Software": "Software",
    "Servicios - Otros": "Otros"
  },
  "SUELDOS": {
    // Nuevas (2025-12-19)
    "Sueldos - Empleados": "Empleados",
    "Sueldos - Cargas Sociales": "Cargas Sociales",
    "Sueldos - Bonificaciones": "Bonificaciones"
  },
  "OTROS": {
    // Existente (backward compatible)
    "Sin_Clasificar": "Sin Clasificar"
  }
};

async function editarMovimiento(id) {
  try {
    // Cargar datos del movimiento desde /api/movimientos (con filtros vacíos)
    const movimientos = await fetchJSON("/api/movimientos?limit=1000");
    const movimiento = movimientos.find(m => m.id === id);

    if (!movimiento) {
      alert("Movimiento no encontrado");
      return;
    }

    movimientoEditando = movimiento;

    // Rellenar formulario del modal
    document.getElementById("edit-descripcion").value = movimiento.descripcion || "";
    document.getElementById("edit-categoria").value = movimiento.categoria || "OTROS";

    // Cargar subcategorías según la categoría
    cargarSubcategorias(movimiento.categoria || "OTROS");
    document.getElementById("edit-subcategoria").value = movimiento.subcategoria || "";

    // Mostrar modal
    document.getElementById("modal-editar").classList.add("show");

  } catch (err) {
    alert(`Error cargando movimiento: ${err.message}`);
  }
}

function cargarSubcategorias(categoria) {
  const selectSubcat = document.getElementById("edit-subcategoria");
  selectSubcat.innerHTML = "";

  const subcats = CATEGORIAS[categoria] || {};

  for (const [key, label] of Object.entries(subcats)) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = label;
    selectSubcat.appendChild(option);
  }
}

async function guardarCambios() {
  if (!movimientoEditando) return;

  const descripcion = document.getElementById("edit-descripcion").value;
  const categoria = document.getElementById("edit-categoria").value;
  const subcategoria = document.getElementById("edit-subcategoria").value;
  const recordarRegla = document.getElementById("recordar-regla").checked;

  try {
    // Construir query params
    const params = new URLSearchParams();
    if (descripcion) params.append("descripcion", descripcion);
    if (categoria) params.append("categoria", categoria);
    if (subcategoria) params.append("subcategoria", subcategoria);

    const res = await fetch(`/api/movimientos/${movimientoEditando.id}?${params.toString()}`, {
      method: "PUT",
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `${res.status} ${res.statusText}`);
    }

    // ETAPA 4: Si el checkbox está marcado, guardar regla aprendida
    if (recordarRegla && descripcion && categoria && subcategoria) {
      try {
        const patron = generarPatronDesdeDescripcion(descripcion);
        await guardarReglaAprendida(patron, categoria, subcategoria);
      } catch (err) {
        console.warn("Error guardando regla aprendida:", err);
        // No bloquear el flujo principal si falla el guardado de regla
      }
    }

    // Cerrar modal
    cerrarModal();

    // Refrescar dashboard
    await initDashboard();

    alert("Movimiento actualizado exitosamente ✅");

  } catch (err) {
    alert(`Error guardando cambios: ${err.message}`);
  }
}

function cerrarModal() {
  movimientoEditando = null;
  document.getElementById("modal-editar").classList.remove("show");
}

async function eliminarMovimiento(id) {
  if (!confirm("¿Estás seguro que querés eliminar este movimiento?\n\nEsta acción no se puede deshacer.")) {
    return;
  }

  try {
    const res = await fetch(`/api/movimientos/${id}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `${res.status} ${res.statusText}`);
    }

    // Refrescar dashboard
    await initDashboard();

    alert("Movimiento eliminado exitosamente ✅");

  } catch (err) {
    alert(`Error eliminando movimiento: ${err.message}`);
  }
}

// Event listener para el select de categoría
document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  initProcesoCompleto();

  // Listener para cambio de categoría en modal
  const selectCat = document.getElementById("edit-categoria");
  if (selectCat) {
    selectCat.addEventListener("change", (e) => {
      cargarSubcategorias(e.target.value);
    });
  }

  // Cerrar modal con ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      cerrarModal();
    }
  });

  // Cerrar modal al hacer click fuera
  const modal = document.getElementById("modal-editar");
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target.id === "modal-editar") {
        cerrarModal();
      }
    });
  }
});

// ============================================
// ETAPA 4: FUNCIONES PARA REGLAS APRENDIBLES
// ============================================

/**
 * Normaliza texto para generar patrones consistentes.
 * Replica la lógica de backend/core/reglas_aprendidas.py
 */
function normalizarTexto(texto) {
  if (!texto) return "";

  // Convertir a mayúsculas
  texto = texto.toUpperCase();

  // Strip inicial
  texto = texto.trim();

  // Remover caracteres especiales (dejar solo letras, números y espacios)
  texto = texto.replace(/[^A-Z0-9\s]/g, '');

  // Reemplazar múltiples espacios por uno solo
  texto = texto.replace(/\s+/g, ' ');

  // Strip final
  texto = texto.trim();

  return texto;
}

/**
 * Genera un patrón desde una descripción de movimiento.
 * Toma las primeras 5 palabras de la descripción normalizada.
 */
function generarPatronDesdeDescripcion(descripcion, maxPalabras = 5) {
  const textoNormalizado = normalizarTexto(descripcion);

  if (!textoNormalizado) return "";

  // Tomar las primeras N palabras
  const palabras = textoNormalizado.split(' ').slice(0, maxPalabras);

  // Unir con espacio
  const patron = palabras.join(' ');

  return patron;
}

/**
 * Guarda una regla aprendida en el backend.
 */
async function guardarReglaAprendida(patron, categoria, subcategoria) {
  const res = await fetch('/api/reglas', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      patron: patron,
      categoria: categoria,
      subcategoria: subcategoria
    })
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `${res.status} ${res.statusText}`);
  }

  const data = await res.json();
  console.log('✅ Regla aprendida guardada:', data);
  return data;
}
