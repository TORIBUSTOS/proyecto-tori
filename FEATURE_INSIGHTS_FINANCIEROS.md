# FEATURE: Insights Financieros/Operativos en Analytics

**Fecha:** 2025-12-19
**Versión:** 2.0.2
**Estado:** ✅ COMPLETADO

## Objetivo

Agregar una sección de **Insights Financieros/Operativos** en la vista Analytics para mostrar lecturas estratégicas del período basadas en datos reales del sistema.

## Características Principales

### Qué son los Insights

- **NO son métricas nuevas** - Complementan los datos existentes con interpretación
- **NO reemplazan gráficos** - Se muestran junto con las visualizaciones
- **NO alteran datos** - Solo leen y analizan información existente
- **Describen PATRONES** del negocio/operación financiera
- **Lenguaje humano** - Fácil de entender
- **Accionables** - Cada insight sugiere una acción concreta

### Tipos de Insights Implementados

1. **Movimientos sin clasificar**
   - Detecta cuando hay >10% de movimientos sin categoría
   - Acción: Corregirlos para mejorar reportes

2. **Concentración de egresos**
   - Identifica categorías que concentran >40% del gasto
   - Acción: Revisar si es recurrente o excepcional

3. **Flujo de caja negativo**
   - Alerta cuando el mes cierra con variación negativa
   - Acción: Evaluar si es estacional o requiere ajustes

4. **Movimiento único detectado**
   - Detecta categorías con solo 1 movimiento en el mes
   - Acción: Verificar si es excepcional o debe reclasificarse

5. **Concentración en top categoría**
   - Identifica cuando una categoría domina >30% de egresos principales
   - Acción: Evaluar dependencia operativa

6. **Crecimiento/Caída significativa**
   - Detecta variaciones >50% vs mes anterior
   - Acción: Identificar drivers o analizar causas

7. **Concentración de ingresos**
   - Alerta cuando una fuente concentra >70% de ingresos
   - Acción: Diversificar para reducir riesgo

## Implementación Técnica

### Backend

**1. Motor de Insights (`backend/core/insights.py`)**
```python
class Insight:
    def __init__(self, lens: str, title: str, message: str, action: str):
        self.lens = lens  # Categoría interna
        self.title = title  # Título visible
        self.message = message  # Descripción (1-2 líneas)
        self.action = action  # Acción sugerida

def generar_insights(reporte: Dict, db: Session, mes: Optional[str]) -> List[Insight]:
    """
    Genera insights basados en:
    - Reporte ejecutivo (fuente de verdad)
    - Movimientos de la base de datos
    - Comparaciones con mes anterior
    """
```

**Características del motor:**
- Máximo 7 insights por período
- Basado en umbrales configurables
- Sin juicios de valor
- Lenguaje neutral y accionable

**2. Endpoint API (`backend/api/routes.py:131-176`)**
```python
@router.get("/insights")
async def obtener_insights(mes: Optional[str] = None):
    """
    GET /api/insights?mes=YYYY-MM

    Response:
    {
        "status": "success",
        "insights": [
            {
                "lens": "clasificacion",
                "title": "Movimientos sin clasificar",
                "message": "Se detectaron 15 movimientos sin categoría (12% del total).",
                "action": "Corregirlos para mejorar reportes y automatismos."
            }
        ],
        "mes": "2024-10"
    }
    """
```

### Frontend

**1. Bloque Visual (`frontend/templates/analytics.html:305-311`)**
```html
<div class="chart-card full-width" id="insights-container">
    <h3>🧠 Insights del Período</h3>
    <div id="insights-content">
        <!-- Se completa dinámicamente por JS -->
    </div>
</div>
```

**2. Estilos CSS (`frontend/templates/analytics.html:215-256`)**
```css
.insight-card {
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 16px;
    margin-bottom: 12px;
    border-radius: 6px;
}

.insight-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
}

.insight-message {
    font-size: 14px;
    color: #475569;
    line-height: 1.5;
}

.insight-action::before {
    content: "Acción: ";
    font-weight: 600;
    color: #3b82f6;
}
```

**3. JavaScript (`frontend/static/js/charts.js:553-602`)**
```javascript
async function cargarYRenderizarInsights(mes) {
    const url = mes ? `${API_URL}/insights?mes=${mes}` : `${API_URL}/insights`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.status === 'success') {
        renderInsights(data.insights);
    }
}

function renderInsights(insights) {
    // Si no hay insights
    if (!insights || insights.length === 0) {
        container.innerHTML = '<div class="no-insights">No se detectaron patrones relevantes en este período.</div>';
        return;
    }

    // Renderizar cards
    const insightsHTML = insights.map(insight => `
        <div class="insight-card">
            <div class="insight-title">${insight.title}</div>
            <div class="insight-message">${insight.message}</div>
            <div class="insight-action">${insight.action}</div>
        </div>
    `).join('');
}
```

## Integración con Sincronización de Período

Los insights están completamente sincronizados con el sistema de selección de período:

```javascript
// En charts.js:cargarGraficos()
async function cargarGraficos() {
    const mes = document.getElementById('mes-selector').value;

    // Cargar gráficos...
    await renderPieIngresos(mes);
    await renderPieEgresos(mes);

    // Cargar resumen ejecutivo...
    const reporte = await fetchReporteEjecutivo(mes);
    renderResumenEjecutivo(reporte);

    // Cargar insights (sincronizado con mismo mes)
    await cargarYRenderizarInsights(mes);
}
```

**Flujo de sincronización:**
1. Usuario cambia selector de período (navbar o interno)
2. Evento `periodoChanged` se dispara
3. `cargarGraficos()` se ejecuta con nuevo mes
4. Insights se recargan automáticamente con mismo mes

## Tests

**Archivo:** `test_insights.py` (5 tests automatizados)

**Tests implementados:**
1. ✅ GET /api/insights (todos los períodos)
2. ✅ GET /api/insights?mes=2024-10 (mes específico)
3. ✅ Límite de 7 insights
4. ✅ Estructura correcta de cada insight
5. ✅ Validación de mes inválido (400 Bad Request)

**Resultados:**
```
============================================================
SUCCESS - TODOS LOS TESTS PASARON
============================================================
```

**Ejemplo de insight generado:**
```json
{
    "lens": "tendencia",
    "title": "Caída significativa",
    "message": "El saldo cayó 100% respecto al mes anterior.",
    "action": "Analizar causas y evaluar medidas correctivas."
}
```

## Archivos Creados/Modificados

### Archivos Nuevos
- `backend/core/insights.py` (~180 líneas) - Motor de generación de insights
- `test_insights.py` (~170 líneas) - Suite de tests
- `FEATURE_INSIGHTS_FINANCIEROS.md` - Esta documentación

### Archivos Modificados
- `backend/api/routes.py` (+47 líneas) - Endpoint /api/insights
- `frontend/templates/analytics.html` (+48 líneas) - HTML + CSS
- `frontend/static/js/charts.js` (+50 líneas) - Carga y renderizado

**Total:** ~500 líneas de código + documentación

## Ubicación en la UI

```
Analytics (/analytics)
├── Selector de Mes
├── Gráficos
│   ├── Pie Chart: Ingresos
│   ├── Pie Chart: Egresos
│   └── Line Chart: Flujo Diario
├── Resumen Ejecutivo (tablas)
└── 🧠 Insights del Período (NUEVO)
    ├── Card 1: Insight tipo 1
    ├── Card 2: Insight tipo 2
    └── ...máximo 7 cards
```

## Comportamiento

### Caso 1: Hay insights
```
🧠 Insights del Período

┌─────────────────────────────────────────────┐
│ Concentración de egresos                     │
│ La categoría 'Prestadores' concentra 65%    │
│ del gasto del mes.                           │
│ Acción: Revisar si es un gasto recurrente  │
│ o excepcional.                               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Movimientos sin clasificar                   │
│ Se detectaron 8 movimientos sin categoría   │
│ (15% del total).                             │
│ Acción: Corregirlos para mejorar reportes   │
│ y automatismos.                              │
└─────────────────────────────────────────────┘
```

### Caso 2: No hay insights
```
🧠 Insights del Período

No se detectaron patrones relevantes en este período.
```

### Caso 3: Error en carga
```
🧠 Insights del Período

No se pudieron cargar los insights.
```

## Criterios de Éxito

- ✅ Analytics muestra gráficos + resumen + insights
- ✅ Los insights cambian al cambiar el período
- ✅ No se rompe ninguna funcionalidad existente
- ✅ Sincronización correcta con selector de período
- ✅ Máximo 7 insights por período
- ✅ Lenguaje humano y accionable
- ✅ No hay placeholders técnicos visibles
- ✅ Tests pasando al 100%

## Ejemplos de Uso

### Usuario cambia período en navbar
```
1. Usuario selecciona "Nov 2024" en navbar
2. Evento periodoChanged se dispara
3. Analytics recarga:
   - Gráficos de Nov 2024
   - Resumen ejecutivo de Nov 2024
   - Insights de Nov 2024
4. Insights muestran patrones específicos del mes
```

### Usuario navega a Analytics
```
1. Usuario abre /analytics
2. Sistema carga período guardado en localStorage
3. Muestra gráficos + resumen + insights
4. Insights detectan automáticamente patrones
```

## Notas de Diseño

### ¿Por qué máximo 7 insights?
- Evita saturación de información
- Prioriza los patrones más relevantes
- Mantiene UI limpia y legible

### ¿Por qué NO son métricas?
- Las métricas ya están en gráficos y resumen ejecutivo
- Los insights INTERPRETAN las métricas
- Agregan valor cualitativo, no cuantitativo

### ¿Por qué lenguaje neutral?
- Evita sesgos en la interpretación
- No hace juicios de valor ("malo", "bueno")
- Se enfoca en HECHOS + ACCIONES

## Próximas Mejoras (Futuro)

1. **Más tipos de insights**
   - Detección de tendencias multi-mes
   - Comparación con promedio histórico
   - Alertas de anomalías

2. **Configuración de umbrales**
   - Permitir al usuario ajustar umbrales (ej: >40% → >50%)
   - Guardar preferencias por usuario

3. **Insights ignorables**
   - Permitir "descartar" insights no relevantes
   - Recordar preferencias

4. **Exportación**
   - Incluir insights en Excel Ejecutivo
   - Agregar sección en PDF

## Conclusión

Los insights financieros/operativos complementan exitosamente la funcionalidad de Analytics, agregando una capa de interpretación estratégica a los datos sin alterar ni reemplazar las visualizaciones existentes.

**Resultado:** Analytics ahora ofrece una experiencia completa con datos (gráficos), resumen ejecutivo (tablas) e interpretación estratégica (insights).

---

**Documentación generada:** 2025-12-19
**Autor:** Claude Code
**Versión:** 1.0
