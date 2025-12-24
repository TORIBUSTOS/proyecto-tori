# FEATURE: Aplicar Reglas Masivamente en /metadata

**Fecha:** 2025-12-22
**Estado:** ✅ COMPLETADO
**Versión:** 1.0

---

## Resumen

Se implementó la funcionalidad de **recategorización masiva** de movimientos desde la pantalla `/metadata`, permitiendo aplicar reglas de categorización de forma selectiva por mes y/o batch.

---

## Objetivos Cumplidos

### 1. ✅ UX: Columna Descripción Clickeable

**Problema:** No estaba claro que solo la columna "Descripción" era clickeable para ver el modal de detalles.

**Solución implementada:**
- Estilo de link azul con underline solo en columna Descripción
- Icono 🔍 agregado a cada celda de descripción
- Tooltip "Ver detalle completo" en hover
- Removido estilo clickeable de columna "Nombre"

**Archivos modificados:**
- `frontend/templates/metadata.html` (líneas 123-139, 448, 462-468)

**CSS agregado:**
```css
td.clickable-descripcion {
  cursor: pointer;
  color: #3b82f6;
  text-decoration: underline;
}

.search-icon {
  margin-right: 6px;
  opacity: 0.7;
}
```

---

### 2. ✅ Backend: Endpoint POST /api/reglas/aplicar

**Funcionalidad:**
- Aplica reglas de categorización masivamente según filtros
- Usa primero reglas aprendidas, luego motor cascada
- Retorna estadísticas detalladas de la operación

**Parámetros del endpoint:**
- `mes` (opcional): Filtrar por mes (formato YYYY-MM) o "all" para todos
- `batch_id` (opcional): Filtrar por batch específico
- `solo_sin_categoria` (opcional): Solo recategorizar movimientos sin categoría
- `solo_confianza_menor_a` (opcional): Solo recategorizar si confianza < valor

**Respuesta exitosa:**
```json
{
  "status": "success",
  "mensaje": "Reglas aplicadas exitosamente: 142 movimientos actualizados",
  "evaluados": 200,
  "actualizados": 142,
  "por_regla_aprendida": 35,
  "por_motor_cascada": 107,
  "porcentaje_actualizados": 71.0,
  "estadisticas": [
    {
      "categoria": "EGRESOS",
      "subcategoria": "Prestadores_Farmacias",
      "count": 45
    },
    ...
  ]
}
```

**Archivos modificados:**
- `backend/api/routes.py` (líneas 1196-1359)

**Lógica del endpoint:**
1. Construye query con filtros (mes, batch_id, sin_categoria, confianza_baja)
2. Obtiene movimientos a procesar
3. Para cada movimiento:
   - Intenta aplicar regla aprendida (prioridad)
   - Si no hay match, aplica motor cascada
   - Solo actualiza si cambió categoría/subcategoría/confianza
4. Hace commit y retorna estadísticas

---

### 3. ✅ Frontend: Botón "Aplicar Reglas" con Modal de Confirmación

**Funcionalidad:**
- Botón destacado "⚡ Aplicar Reglas" en toolbar de filtros
- Modal de confirmación mostrando alcance de la operación
- Toast de notificación con resultado
- Recarga automática de tabla después de aplicar

**Componentes agregados:**

1. **Botón en toolbar** (línea 348-350):
```html
<button id="btnAplicarReglas" class="btn-action btn-primary">
  ⚡ Aplicar Reglas
</button>
```

2. **Modal de confirmación** (líneas 395-405):
- Muestra período/batch afectado
- Informa acción a realizar
- Botones Cancelar/Confirmar

3. **Toast de notificación** (líneas 407-411):
- Success: Verde con borde
- Error: Rojo con borde
- Auto-desaparece en 5 segundos

**JavaScript agregado:**
- `mostrarToast(titulo, mensaje, tipo)` (líneas 734-750)
- `aplicarReglasMasivas()` (líneas 755-786): Abre modal con detalles
- `confirmarAplicarReglas()` (líneas 791-854): Ejecuta POST y muestra resultado

**Flujo de usuario:**
1. Usuario selecciona filtros (Vista + Archivo)
2. Click en "⚡ Aplicar Reglas"
3. Modal muestra detalles:
   - 📅 Período: 2025-11
   - 📁 Archivo: extracto_noviembre.xlsx
   - ⚡ Acción: Recategorizar usando reglas aprendidas + motor cascada
4. Usuario confirma
5. Toast muestra: "⏳ Procesando..."
6. Al completar: "✅ 142 de 200 movimientos recategorizados (71%)"
7. Tabla se recarga con nuevas categorizaciones

---

## Estilos CSS Agregados

**Botones de acción** (líneas 141-167):
- `.btn-action`: Estilo base para botones
- `.btn-primary`: Gradiente azul para botón principal

**Modal de confirmación** (líneas 169-228):
- Centrado en pantalla
- Fondo blanco con sombra
- Botones Cancel/Confirm estilizados

**Toast de notificación** (líneas 230-261):
- Posicionado top-right
- Borde izquierdo de color según tipo
- Auto-desaparece

---

## Casos de Uso

### Caso 1: Recategorizar mes completo
```
1. Usuario selecciona Vista = "Mes actual" (Noviembre 2025)
2. Click en "⚡ Aplicar Reglas"
3. Modal confirma: "Período: 2025-11"
4. Confirmar
5. Resultado: 200 movimientos evaluados, 142 actualizados
```

### Caso 2: Recategorizar archivo específico
```
1. Usuario selecciona Archivo = "extracto_octubre.xlsx"
2. Click en "⚡ Aplicar Reglas"
3. Modal confirma: "Archivo: extracto_octubre.xlsx"
4. Confirmar
5. Resultado: 85 movimientos evaluados, 62 actualizados
```

### Caso 3: Recategorizar todo
```
1. Usuario selecciona Vista = "Todo lo cargado"
2. Click en "⚡ Aplicar Reglas"
3. Modal confirma: "Ámbito: Todos los movimientos"
4. Confirmar
5. Resultado: 3,848 movimientos evaluados, 2,100 actualizados
```

---

## Testing

### Script de prueba
- Archivo: `test_aplicar_reglas.py`
- Tests implementados:
  1. ✅ Aplicar reglas sin filtros (todos)
  2. ✅ Aplicar reglas por mes específico
  3. ✅ Aplicar reglas por batch específico
  4. ✅ Aplicar reglas con filtros combinados
  5. ✅ Formato de mes inválido (debe fallar 400)
  6. ✅ Aplicar reglas con mes="all"

### Ejecución:
```bash
python test_aplicar_reglas.py
```

**Nota:** Los tests MODIFICAN la base de datos. Ejecutar de a uno por vez.

---

## Archivos Modificados

### Backend
- ✅ `backend/api/routes.py` (+164 líneas)
  - Nuevo endpoint POST /api/reglas/aplicar (líneas 1196-1359)

### Frontend
- ✅ `frontend/templates/metadata.html` (+280 líneas aprox)
  - CSS para botones, modal, toast (líneas 141-261)
  - Botón "Aplicar Reglas" (líneas 348-350)
  - Modal de confirmación HTML (líneas 395-405)
  - Toast HTML (líneas 407-411)
  - JavaScript para aplicar reglas (líneas 731-870)
  - UX fix para columna Descripción clickeable (líneas 123-139, 448)

### Testing
- ✅ `test_aplicar_reglas.py` (nuevo archivo, 185 líneas)

### Documentación
- ✅ `FEATURE_APLICAR_REGLAS_MASIVO.md` (este archivo)

---

## Beneficios

### Para el Usuario
- ✅ **Control granular:** Puede recategorizar por mes o por archivo específico
- ✅ **Transparencia:** Modal muestra exactamente qué se va a hacer
- ✅ **Feedback inmediato:** Toast muestra resultado con estadísticas
- ✅ **Seguridad:** Confirmación antes de aplicar cambios masivos
- ✅ **UX mejorado:** Claro qué columna es clickeable (Descripción con 🔍)

### Para el Sistema
- ✅ **Eficiencia:** Procesamiento masivo en una sola operación
- ✅ **Inteligencia:** Usa reglas aprendidas primero, luego motor cascada
- ✅ **Estadísticas:** Retorna breakdown detallado por categoría
- ✅ **Flexibilidad:** Múltiples filtros combinables

---

## Próximas Mejoras (Opcionales)

### 1. Opciones de Filtrado Avanzado
```javascript
// Agregar checkboxes en modal de confirmación:
☐ Solo movimientos sin categoría
☐ Solo si confianza < 50%
```

### 2. Preview de Cambios
```javascript
// Mostrar tabla preview de cambios antes de confirmar:
Descripción         | Categoría Actual  → Nueva
─────────────────────────────────────────────────
Transferencia...    | SIN_CATEGORIA     → TRANSFERENCIAS
Farmacia X...       | OTROS            → EGRESOS:Prestadores
```

### 3. Deshacer Última Aplicación
```javascript
// Botón "⏪ Deshacer última recategorización"
// Guardar snapshot antes de aplicar reglas
```

### 4. Exportar Estadísticas
```javascript
// Botón "📊 Exportar estadísticas a CSV"
// Descargar breakdown completo de categorizaciones
```

---

## Notas Técnicas

### ¿Por qué primero reglas aprendidas?
- **Mayor precisión:** Las reglas aprendidas son específicas del usuario
- **Contexto:** Se basan en ediciones manuales previas
- **Confianza:** Tienen mayor confianza que reglas genéricas

### ¿Por qué modal de confirmación?
- **Prevención de errores:** Operaciones masivas son irreversibles
- **Transparencia:** Usuario sabe exactamente qué va a pasar
- **Compliance:** Buena práctica de UX para operaciones destructivas

### ¿Por qué toast en vez de alert()?
- **No bloqueante:** Permite seguir trabajando
- **Estético:** Integrado con el diseño del sistema
- **Informativo:** Muestra estadísticas detalladas

---

## Conclusión

La funcionalidad de **recategorización masiva** está completamente implementada y probada. Permite a los usuarios aplicar reglas de categorización de forma selectiva y controlada, con feedback claro del resultado.

**Resultado:** Sistema de categorización masiva profesional con UX mejorado. 🎯

---

**Autor:** Claude Code
**Fecha:** 2025-12-22
**Versión:** 1.0
