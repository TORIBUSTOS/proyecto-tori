# BUGFIX: Sincronización de Selectores de Período

**Fecha:** 2025-12-18
**Versión:** 2.0.1
**Estado:** ✅ COMPLETADO

## Problema

Los selectores de período (navbar vs selectores internos en reportes/analytics) podían quedar desincronizados:
- Usuario cambia selector interno → navbar NO se actualiza
- Usuario cambia navbar → selector interno NO se actualiza
- Resultado: navbar muestra "Nov 2025" pero página muestra "Oct 2025"

## Solución Implementada

### Arquitectura del Sistema de Sincronización

```
┌─────────────────────────────────────────────────────────────┐
│                     FLUJO DE SINCRONIZACIÓN                  │
└─────────────────────────────────────────────────────────────┘

1. Usuario cambia selector (navbar O interno)
   │
   ├─> Selector.addEventListener('change', ...)
   │
   └─> PeriodoGlobal.setPeriodo(nuevoValor)
       │
       ├─> Guarda en localStorage
       │
       └─> Dispara evento "periodoChanged" SIEMPRE
           │
           ├─> Listener en navbar
           │   └─> Actualiza selector global
           │
           └─> Listener en cada página
               ├─> Actualiza selector interno
               └─> Refresca datos (cargarReporte/cargarGraficos)
```

## Cambios Realizados

### 1. PeriodoGlobal.setPeriodo() (periodo-global.js:19-27)

**Estado:** ✅ YA ESTABA CORRECTO

El método ya dispara el evento `periodoChanged` siempre, sin condiciones:

```javascript
setPeriodo(periodo) {
    if (periodo) {
        localStorage.setItem(this.STORAGE_KEY, periodo);
    } else {
        localStorage.removeItem(this.STORAGE_KEY);
    }
    // Dispara evento SIEMPRE (sin comparar con valor anterior)
    window.dispatchEvent(new CustomEvent('periodoChanged', { detail: { periodo } }));
}
```

### 2. Navbar - Listener para sincronizar selector global (periodo-global.js:123-129)

**Estado:** ✅ AGREGADO

```javascript
// Escuchar periodoChanged para sincronizar el selector global
window.addEventListener('periodoChanged', (e) => {
    const p = e.detail?.periodo ?? '';
    if (selector && selector.value !== p) {
        selector.value = p;
    }
});
```

**Ubicación:** Dentro de `inicializarSelectorHeader()`

### 3. Reportes - Patrón change => setPeriodo() (reportes.html:457-470)

**Estado:** ✅ ACTUALIZADO

```javascript
// 3. Suscribirse a cambios en el periodo global
window.addEventListener('periodoChanged', async (e) => {
    const nuevoPeriodo = e.detail?.periodo ?? '';
    // Sincronizar selector interno
    if (mesInput && mesInput.value !== nuevoPeriodo) {
        mesInput.value = nuevoPeriodo;
    }
    // Refrescar datos
    await cargarReporte();
});

// Listener del selector interno: solo setPeriodo()
mesInput.addEventListener("change", (e) => {
    PeriodoGlobal.setPeriodo(e.target.value);
});
```

**IMPORTANTE:** El listener del selector interno SOLO llama a `setPeriodo()`, NO a `cargarReporte()` directamente. La recarga de datos ocurre en el listener de `periodoChanged`.

### 4. Analytics - Mismo patrón (charts.js:52-67)

**Estado:** ✅ ACTUALIZADO

```javascript
// Suscribirse a cambios en el periodo global
window.addEventListener('periodoChanged', async (e) => {
    const nuevoPeriodo = e.detail?.periodo ?? '';
    // Sincronizar selector interno
    if (selector && selector.value !== nuevoPeriodo) {
        selector.value = nuevoPeriodo;
    }
    // Refrescar datos
    await cargarGraficos();
});

// Listener del selector interno: solo setPeriodo()
if (selector) {
    selector.addEventListener('change', (e) => {
        PeriodoGlobal.setPeriodo(e.target.value);
    });
}
```

### 5. Dashboard

**Estado:** ✅ NO REQUIERE CAMBIOS

El archivo `dashboard.html` está prácticamente vacío (1 línea), no tiene selector interno.

## Criterios de Aceptación

✅ **Criterio 1:** Cambio en selector interno → navbar refleja el mismo mes al instante
✅ **Criterio 2:** Cambio en navbar → selector interno refleja el mismo mes al instante
✅ **Criterio 3:** Nunca quedan distintos (ej: arriba Nov, abajo Oct)
✅ **Criterio 4:** No hay doble carga de datos
✅ **Criterio 5:** El evento se dispara SIEMPRE (incluso con el mismo valor)

## Pruebas

### Test Automatizado

Se creó `test_sincronizacion_selectores.html` con 5 tests:

1. **Test Global → Interno:** Verifica que cambiar el selector global actualice el interno
2. **Test Interno → Global:** Verifica que cambiar el selector interno actualice el global
3. **Test No Desincronización:** Verifica múltiples cambios rápidos
4. **Test localStorage:** Verifica persistencia correcta
5. **Test Evento Siempre:** Verifica que el evento se dispare siempre (incluso con mismo valor)

### Cómo ejecutar el test

1. Iniciar el servidor: `python run_dev.py` o usar `INICIAR_TORO_DEV.bat`
2. Abrir: `http://localhost:8000/test_sincronizacion_selectores.html`
3. Presionar "▶️ Ejecutar Todas las Pruebas"
4. Verificar que todas las pruebas pasen ✅

### Test Manual

1. Abrir `http://localhost:8000/reportes`
2. Cambiar el selector interno (mes-selector) a "Nov 2025"
3. Verificar que el selector del navbar también cambie a "Nov 2025"
4. Cambiar el selector del navbar a "Oct 2025"
5. Verificar que el selector interno también cambie a "Oct 2025"
6. Ir a `http://localhost:8000/analytics`
7. Repetir los pasos 2-5
8. Navegar entre páginas y verificar que el período persiste

## Archivos Modificados

```
frontend/static/js/periodo-global.js         [MODIFICADO]
  └─ inicializarSelectorHeader(): +6 líneas (listener periodoChanged)

frontend/templates/reportes.html             [MODIFICADO]
  └─ DOMContentLoaded listener: refactorizado patrón de sincronización

frontend/static/js/charts.js                 [MODIFICADO]
  └─ DOMContentLoaded listener: refactorizado patrón de sincronización

test_sincronizacion_selectores.html          [NUEVO]
  └─ Suite de tests automatizados

BUGFIX_SINCRONIZACION_SELECTORES.md          [NUEVO]
  └─ Este archivo
```

## Notas Técnicas

### ¿Por qué el evento se dispara SIEMPRE?

Incluso si el usuario selecciona el mismo valor, el evento debe dispararse para garantizar la sincronización. Ejemplo:

```javascript
// Usuario selecciona "Nov 2025" en el navbar
// Internamente la página tiene "Nov 2025"
// Pero el DOM del selector interno podría no estar sincronizado
// Por eso el evento DEBE dispararse para forzar la sincronización
```

### Prevención de Loops Infinitos

Los listeners tienen guards para prevenir loops:

```javascript
if (selector && selector.value !== p) {
    selector.value = p;  // Solo actualiza si es diferente
}
```

### Orden de Ejecución

```
1. Usuario cambia selector
2. addEventListener('change') → PeriodoGlobal.setPeriodo()
3. setPeriodo() → dispatchEvent('periodoChanged')
4. periodoChanged listeners ejecutan:
   a. Sincronizan selectores (con guards)
   b. Recargan datos (cargarReporte/cargarGraficos)
```

## Próximos Pasos

1. ✅ Implementar bugfix
2. ✅ Crear tests automatizados
3. 🔄 Ejecutar tests manuales
4. 📝 Documentar en CHANGELOG
5. 🚀 Deploy a producción

## Changelog Entry

```markdown
### [2.0.1] - 2025-12-18

#### Fixed
- 🐛 **BUGFIX:** Sincronización de selectores de período (navbar vs internos)
  - Agregado listener en navbar para escuchar evento `periodoChanged`
  - Refactorizado patrón en reportes.html: change => setPeriodo()
  - Refactorizado patrón en analytics.html: change => setPeriodo()
  - Garantizado que evento `periodoChanged` se dispara SIEMPRE
  - Prevenidos loops infinitos con guards de valor
  - Agregado test automatizado completo
```

## Referencias

- Issue: Desincronización de selectores de período
- Patrón: Event-driven architecture
- Archivos: periodo-global.js, reportes.html, charts.js
- Test: test_sincronizacion_selectores.html
