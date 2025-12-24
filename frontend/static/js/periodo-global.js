(function () {
  const params = new URLSearchParams(window.location.search);

  function getPeriod() {
    return (
      params.get("period") ||
      localStorage.getItem("period") ||
      null
    );
  }

  function setPeriod(period, reload = true) {
    if (!period) return;

    params.set("period", period);
    localStorage.setItem("period", period);

    const newUrl =
      window.location.pathname + "?" + params.toString();

    if (reload) {
      window.location.href = newUrl;
    } else {
      history.replaceState({}, "", newUrl);
    }
  }

  async function cargarPeriodos() {
    try {
      const res = await fetch('/api/periodos');
      const data = await res.json();

      // Aplanar períodos agrupados por año
      const periodos = [];
      if (data.periodos && typeof data.periodos === 'object') {
        Object.values(data.periodos).forEach(arr => {
          if (Array.isArray(arr)) {
            periodos.push(...arr);
          }
        });
      }

      return periodos.sort().reverse();
    } catch (error) {
      console.error('Error cargando períodos:', error);
      return [];
    }
  }

  async function inicializar() {
    const periodos = await cargarPeriodos();
    const currentPeriod = getPeriod();

    // Poblar selector GLOBAL
    const globalSelect = document.getElementById("periodo-global");
    if (globalSelect) {
      // Limpiar opciones existentes excepto la primera
      globalSelect.innerHTML = '<option value="">Todos los periodos</option>';

      // Agregar períodos
      periodos.forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        globalSelect.appendChild(option);
      });

      // Seleccionar período actual o el más reciente
      if (currentPeriod && periodos.includes(currentPeriod)) {
        globalSelect.value = currentPeriod;
      } else if (periodos.length > 0 && !currentPeriod) {
        // Si no hay período seleccionado, usar el más reciente
        const maReciente = periodos[0];
        globalSelect.value = maReciente;
        setPeriod(maReciente, false);
      }

      // Listener para cambios
      globalSelect.addEventListener("change", () => {
        setPeriod(globalSelect.value, true);
      });
    }

    // Poblar selector ANALYTICS
    const analyticsSelect = document.getElementById("mes");
    if (analyticsSelect) {
      // Mantener la opción "Todos los períodos"
      periodos.forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        analyticsSelect.appendChild(option);
      });

      // Seleccionar período actual
      if (currentPeriod && periodos.includes(currentPeriod)) {
        analyticsSelect.value = currentPeriod;
      }

      // Listener para cambios
      analyticsSelect.addEventListener("change", () => {
        const value = analyticsSelect.value;

        if (value === "") {
          params.delete("period");
          localStorage.removeItem("period");
          history.replaceState({}, "", window.location.pathname);
          return;
        }

        setPeriod(value, false);
      });
    }

    // Poblar selector REPORTES
    const reportesSelect = document.getElementById("mes-selector");
    if (reportesSelect) {
      // Limpiar opciones existentes excepto la primera
      reportesSelect.innerHTML = '<option value="">Todos los períodos</option>';

      periodos.forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        reportesSelect.appendChild(option);
      });

      // Seleccionar período actual
      if (currentPeriod && periodos.includes(currentPeriod)) {
        reportesSelect.value = currentPeriod;
      }

      // Listener para cambios
      reportesSelect.addEventListener("change", () => {
        const value = reportesSelect.value;

        if (value === "") {
          params.delete("period");
          localStorage.removeItem("period");
          history.replaceState({}, "", window.location.pathname);
          return;
        }

        setPeriod(value, false);
      });
    }
  }

  // Ejecutar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
  } else {
    inicializar();
  }

})();
