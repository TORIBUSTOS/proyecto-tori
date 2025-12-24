# BUGFIX: Analytics vs Reportes - Totales Coincidentes

**Fecha:** 2025-12-18
**Estado:** ✅ COMPLETADO
**Problema:** Los gráficos de `/analytics` no coincidían con `/reportes` (signos y totales diferentes)

---

## Problema Identificado

### Antes del fix:

1. **`/api/analytics/pie-ingresos`**: Agrupaba por `subcategoria` filtrando `categoria == "INGRESOS"`
2. **`/api/analytics/pie-egresos`**: Agrupaba por `subcategoria` filtrando `categoria == "EGRESOS"`
3. **`/api/analytics/flujo-diario`**: Filtraba por `categoria == "INGRESOS"` y `categoria == "EGRESOS"`

### El problema:
- Los endpoints de analytics usaban **SQL directo** con lógica propia
- `/api/reportes` usaba `generar_reporte_ejecutivo()` que filtra por **signo del monto** (`monto > 0` vs `monto < 0`)
- Esto generaba **diferencias en totales** entre analytics y reportes

---

## Solución Implementada

### 1. Backend (`backend/api/routes.py`)

#### ✅ Endpoint `/api/analytics/pie-ingresos` (líneas 580-626)
**ANTES:**
```python
query = db.query(
    Movimiento.subcategoria,
    func.sum(Movimiento.monto).label('total')
).filter(
    Movimiento.categoria == "INGRESOS"
)
```

**DESPUÉS:**
```python
# Usar la misma fuente de verdad que /api/reportes
reporte = generar_reporte_ejecutivo(db, mes)
desglose_ingresos = reporte.get("desglose_ingresos", [])

data = [
    {
        "label": item["categoria"],
        "value": item["monto"]
    }
    for item in desglose_ingresos
]

total = reporte["saldos"]["ingresos_total"]
```

**Beneficios:**
- ✅ Usa la misma lógica que `/api/reportes`
- ✅ Total garantizado positivo
- ✅ Agrupa por `categoria` (no subcategoria)

---

#### ✅ Endpoint `/api/analytics/pie-egresos` (líneas 632-678)
**ANTES:**
```python
query = db.query(
    Movimiento.subcategoria,
    func.sum(Movimiento.monto).label('total')
).filter(
    Movimiento.categoria == "EGRESOS"
)
```

**DESPUÉS:**
```python
# Usar la misma fuente de verdad que /api/reportes
reporte = generar_reporte_ejecutivo(db, mes)
desglose_egresos = reporte.get("desglose_egresos", [])

data = [
    {
        "label": item["categoria"],
        "value": item["monto"]  # Ya viene en valor absoluto
    }
    for item in desglose_egresos
]

total = reporte["saldos"]["egresos_total"]
```

**Beneficios:**
- ✅ Usa la misma lógica que `/api/reportes`
- ✅ Total garantizado positivo (abs)
- ✅ Agrupa por `categoria` (no subcategoria)

---

#### ✅ Endpoint `/api/analytics/flujo-diario` (líneas 684-758)
**ANTES:**
```python
ingresos_query = db.query(...).filter(
    Movimiento.categoria == "INGRESOS",
    func.strftime('%Y-%m', Movimiento.fecha) == mes
)
```

**DESPUÉS:**
```python
# Query para ingresos agrupados por día (monto > 0)
ingresos_query = db.query(...).filter(
    Movimiento.monto > 0,
    func.strftime('%Y-%m', Movimiento.fecha) == mes
)

# Query para egresos agrupados por día (monto < 0)
egresos_query = db.query(...).filter(
    Movimiento.monto < 0,
    func.strftime('%Y-%m', Movimiento.fecha) == mes
)
```

**Beneficios:**
- ✅ Filtra por **signo del monto** (igual que `generar_reporte_ejecutivo`)
- ✅ No depende de categorización previa
- ✅ Consistencia visual y de signos

---

### 2. Frontend (`frontend/static/js/charts.js`)

#### ✅ Función `renderPieIngresos()` (líneas 168-230)
**ANTES:**
```javascript
const data = await res.json();
chartIngresos = new Chart(ctx, {
    data: {
        labels: data.labels,
        datasets: [{
            data: data.data,
            ...
        }]
    }
});
```

**DESPUÉS:**
```javascript
const responseData = await res.json();

// Extraer labels y values del nuevo formato
const labels = responseData.data.map(item => item.label);
const values = responseData.data.map(item => item.value);

chartIngresos = new Chart(ctx, {
    data: {
        labels: labels,
        datasets: [{
            data: values,
            ...
        }]
    }
});
```

**Cambio de formato:**
- **ANTES:** `{labels: [...], data: [...]}`
- **DESPUÉS:** `{status: "success", data: [{label, value}, ...], total: ...}`

---

#### ✅ Función `renderPieEgresos()` (líneas 235-297)
Misma lógica que `renderPieIngresos()`:
- Extrae `labels` y `values` del nuevo formato `{label, value}`
- Mantiene compatibilidad con Chart.js

---

### 3. Testing

Se crearon dos scripts de test:

#### `test_analytics_simple.py`
Test automatizado que verifica:
- ✅ Total ingresos de `/analytics/pie-ingresos` == Total ingresos de `/reportes`
- ✅ Total egresos de `/analytics/pie-egresos` == Total egresos de `/reportes`
- ✅ Formato de respuesta correcto: `{status, data, total}`

**Uso:**
```bash
python test_analytics_simple.py
```

---

## Formato de Respuesta

### Antes:
```json
{
  "labels": ["Cat1", "Cat2"],
  "data": [100.50, 200.75],
  "total": 301.25,
  "mes": "2024-10"
}
```

### Después (nuevo formato):
```json
{
  "status": "success",
  "data": [
    {"label": "Cat1", "value": 100.50},
    {"label": "Cat2", "value": 200.75}
  ],
  "total": 301.25
}
```

---

## Restricciones Respetadas

✅ **No se modificaron los cálculos de `generar_reporte_ejecutivo()`**
✅ **Analytics usa la misma fuente de verdad que /reportes**
✅ **Totales positivos para ingresos y egresos**
✅ **Signos consistentes en gráficos y resumen**

---

## Instrucciones de Despliegue

### 1. Reiniciar el servidor backend
```bash
# Detener el servidor actual (Ctrl+C si está corriendo)

# Iniciar servidor
python run.py
# o
python run_dev.py
```

### 2. Verificar que funciona
```bash
# Test automático
python test_analytics_simple.py

# Test manual
curl "http://localhost:8000/api/analytics/pie-ingresos?mes=2025-11"
curl "http://localhost:8000/api/reportes?mes=2025-11"
```

### 3. Limpiar caché del navegador
- Abrir DevTools (F12)
- Clic derecho en el botón de refrescar
- Seleccionar "Empty Cache and Hard Reload"

---

## Archivos Modificados

### Backend
- ✅ `backend/api/routes.py` (líneas 580-758)
  - Endpoints: `/analytics/pie-ingresos`, `/analytics/pie-egresos`, `/analytics/flujo-diario`

### Frontend
- ✅ `frontend/static/js/charts.js` (líneas 168-297)
  - Funciones: `renderPieIngresos()`, `renderPieEgresos()`

### Testing
- ✅ `test_analytics_simple.py` (nuevo)
- ✅ `test_analytics_fix.py` (nuevo, con colores - puede tener problemas de encoding en Windows)

---

## Resultado Esperado

### Después del fix:

1. **Pie Chart Ingresos**: Total coincide exactamente con "Total Ingresos" de `/reportes`
2. **Pie Chart Egresos**: Total coincide exactamente con "Total Egresos" de `/reportes`
3. **Flujo Diario**: Suma de ingresos/egresos coincide con totales del reporte
4. **Signos consistentes**: Todos los valores mostrados son positivos (visual)

### Verificación Visual:
- Abrir `/analytics`
- Abrir `/reportes`
- Comparar:
  - "Total ingresos" debe ser idéntico
  - "Total egresos" debe ser idéntico
  - Ambos deben ser números positivos

---

## Notas Técnicas

### ¿Por qué filtramos por `monto > 0` en lugar de `categoria == "INGRESOS"`?

El reporte ejecutivo (`backend/core/reportes.py` líneas 61-77) calcula:
```python
# Total ingresos (monto > 0)
ingresos_total = db.query(func.sum(Movimiento.monto)).filter(
    Movimiento.monto > 0
).scalar() or 0.0

# Total egresos (abs de monto < 0)
egresos_sum = db.query(func.sum(Movimiento.monto)).filter(
    Movimiento.monto < 0
).scalar() or 0.0
egresos_total = abs(egresos_sum)
```

Esta es la **fuente de verdad** del sistema. Analytics debe usar la misma lógica para garantizar coincidencia.

---

## Estado Final

✅ **BUGFIX COMPLETADO**
✅ **Todos los endpoints actualizados**
✅ **Frontend adaptado al nuevo formato**
✅ **Scripts de test creados**

**Próximo paso:** Reiniciar el servidor y validar en navegador.
