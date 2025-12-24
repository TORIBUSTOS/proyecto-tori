# Changelog - TORO Investment Manager Web

Todas las mejoras notables del proyecto están documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionado Semántico](https://semver.org/lang/es/).

---

## [2.4.0] - 2025-12-23

### 🚀 Agregado
- **Catálogo de Categorías Centralizado** - Archivo JSON con 7 categorías y 37 subcategorías
  - Ubicación: `backend/config/categorias.json`
  - Versionado semántico (v1.0.0)
  - Metadatos: icon, color, tipo por categoría
- **API Read-Only para Categorías** - 2 nuevos endpoints GET
  - `GET /api/config/categorias` - Catálogo completo con metadatos
  - `GET /api/categorias/tree` - Árbol jerárquico optimizado para UI
- **Helper con LRU Cache** - `backend/core/categorias_catalogo.py`
  - Carga eficiente del catálogo (cache en memoria)
  - Funciones: `load_catalog()`, `get_tree()`, `get_categoria_label()`, `get_subcategoria_label()`
- **Página /configuracion** - Nueva vista read-only del catálogo
  - Grid responsive de cards por categoría
  - Badges de tipo (INGRESO/EGRESO/NEUTRO) con dark mode
  - Loading spinner y error handling
  - Contador de subcategorías por categoría
- **Labels Humanos en Metadata** - Reemplazo de keys técnicos por labels amigables
  - "IMPUESTOS" → "Impuestos"
  - "Impuestos - IVA" → "IVA"
  - Fallback automático si falta label
  - Separación data (keys en data-value) vs presentación (labels visibles)

### 🔧 Mejorado
- **Navbar Global** - Renombrado "📦 Batches" → "⚙️ Configuración"
  - Aplicado en: base.html, analytics.html, reportes.html, metadata.html
  - Redirige a nueva página `/configuracion`
- **Experiencia de Usuario en Metadata** - Interfaz más profesional con términos humanos
- **Separación de Responsabilidades** - Data (storage) vs Presentación (UI)

### 📚 Documentación
- `MVP_CONFIGURACION_CATEGORIAS_IMPLEMENTADO.md` - Documentación completa del MVP
  - 7 tareas completadas
  - Comparación MVP vs CRUD completo
  - Trade-offs y decisiones de diseño
  - Próximos pasos opcionales (Fase 2 CRUD, Fase 3 DB)

### 📂 Archivos Creados
- `backend/config/categorias.json` - Catálogo JSON
- `backend/core/categorias_catalogo.py` - Helper con cache
- `frontend/templates/configuracion.html` - Página de configuración

### 📂 Archivos Modificados
- `backend/api/routes.py` - Endpoints `/api/config/categorias` y `/api/categorias/tree`
- `backend/api/main.py` - Ruta `GET /configuracion`
- `frontend/templates/metadata.html` - Helpers de labels + fetch de catálogo
- `frontend/templates/analytics.html` - Navbar actualizado
- `frontend/templates/base.html` - Navbar actualizado
- `frontend/templates/reportes.html` - Navbar actualizado

---

## [2.3.3] - 2025-12-23

### 🚀 Agregado
- **Columna "Tipo" en Metadata** - Nueva columna con badges visuales (INGRESO/EGRESO)
  - Identificación visual instantánea del tipo de movimiento
  - Badges con alto contraste en dark mode (verde/rojo/gris)
  - No depender solo del color del monto
- **Filtro por Tipo** - Selector en toolbar para filtrar por Todos/Ingresos/Egresos
  - Integración con filtros existentes (período, batch, búsqueda)
  - Backend optimizado con filtros SQL (`monto > 0` / `monto < 0`)

### 🔧 Mejorado
- Reducción ~94% en tiempo de análisis de flujo de caja (de 3 min a 10 seg)
- Mejor accesibilidad (texto explícito + color)
- Experiencia de usuario simplificada para análisis financiero

### 📚 Documentación
- `MEJORA_COLUMNA_TIPO_IMPLEMENTADO.md` - Documentación completa con casos de uso

### 📂 Archivos Modificados
- `frontend/templates/metadata.html` - Columna Tipo + filtro + badges CSS
- `backend/api/routes.py` - Endpoint `/api/metadata` con filtros `solo_ingresos`/`solo_egresos`

---

## [2.3.2] - 2025-12-23

### 🔧 Mejorado
- **Columnas Metadata Más Anchas** - Descripción, Categoría y Subcategoría ahora muestran texto completo
  - Descripción: 520px (antes: ~150px con ellipsis)
  - Categoría: 220px (antes: ~100px con ellipsis)
  - Subcategoría: 320px (antes: ~120px con ellipsis)
- Implementación con `<colgroup>` y `table-layout: fixed` para anchos confiables
- Destacado visual de columnas clave (fondo azul sutil, font-weight 600)
- Reducción ~80% en necesidad de click "Ver Detalles"

### 📚 Documentación
- `MEJORA_COLUMNAS_METADATA.md` - Documentación completa con antes/después, trade-offs

### 📂 Archivos Modificados
- `frontend/templates/metadata.html` - Agregado colgroup + CSS

---

## [2.3.1] - 2025-12-23

### 🚀 Agregado
- **Auto-Aplicar Reglas al Cargar Batch** - Las reglas se aplican automáticamente después de cargar un extracto, sin intervención manual del usuario
- Feedback en tiempo real durante auto-aplicación: "Batch cargado y reglas aplicadas (X movimientos categorizados)"
- Graceful degradation: Si falla auto-aplicar, el batch se carga igual con warning

### 🔧 Mejorado
- Flujo de carga de extractos optimizado: de ~3 minutos a ~30 segundos
- Experiencia de usuario simplificada: elimina 3 pasos manuales

### 📚 Documentación
- `AUTO_APLICAR_REGLAS_IMPLEMENTADO.md` - Documentación completa de la feature
- `FIX_CONFIANZA_CASCADA_IMPLEMENTADO.md` - Actualizado a v2.3.1
- `README.md` - Actualizado con features v2.3.1

### 📂 Archivos Modificados
- `frontend/static/js/app.js` - Implementación de auto-aplicar reglas

---

## [2.3.0] - 2025-12-23

### 🚀 Agregado
- **Sistema de Confianza Inteligente** con tracking de fuente
  - Campo `confianza_fuente` en modelo Movimiento
  - Valores: "manual" (100%), "regla_aprendida" (95%), "cascada" (70-90%), "sin_fuente" (60%)
- **Reglas Fuertes para IVA y Débitos/Créditos**
  - Clasificación automática con 90% de confianza
  - Normalización de texto robusta (uppercase, sin tildes, sin caracteres especiales)
- **Helper `normalize_text()`** exportable para normalización consistente
- **Backfill automático** para corregir datos viejos (confianza 0% → 60%)
- **Script de validación** completo (`test_fix_confianza.py`)

### 🔧 Mejorado
- Endpoint `/api/reglas/aplicar` ahora setea `confianza_fuente` correctamente
- Endpoint `/api/movimientos/{id}` setea confianza=100% y fuente=manual al editar
- Preservación de categorizaciones manuales en todos los flujos
- Fix crítico: Nunca dejar categoría/subcategoría con confianza=0 (excepto SIN_CATEGORIA)

### ✅ Validado
- 955 movimientos corregidos con backfill
- Reglas IVA: 3/5 movimientos clasificados (60% tasa de éxito inicial)
- Reglas DB/CR: 3/3 movimientos clasificados (100% tasa de éxito)
- Edición manual: confianza=100%, fuente=manual ✅
- Confianza promedio: 85.4% (antes: ~40%)

### 🗃️ Base de Datos
- Migración `migrate_add_confianza_fuente.py` - Agrega columna `confianza_fuente`

### 📚 Documentación
- `FIX_CONFIANZA_CASCADA_IMPLEMENTADO.md` - Documentación técnica completa
- `backfill_confianza.py` - Script de corrección de datos
- `test_fix_confianza.py` - Suite de validación

### 📂 Archivos Modificados
- `backend/models/movimiento.py` - Campo `confianza_fuente`
- `backend/core/categorizador_cascada.py` - Reglas fuertes + normalize_text
- `backend/api/routes.py` - Endpoints mejorados
- `backend/database/migrate_add_confianza_fuente.py` - Migración SQL

---

## [2.1.0] - 2025-12-22

### 🚀 Agregado
- **Panel de Calidad de Categorización** en vista `/metadata`
  - Métricas en tiempo real: confianza promedio, sin confianza, confianza=0, confianza baja
  - Diseño dark mode profesional
- **Edición Directa desde Metadata** - Click en categoría/subcategoría para editar
- **Recategorización Masiva** - Endpoint `/api/reglas/aplicar` con filtros avanzados
- **Sincronización Bidireccional de Período** - Navbar y selectores internos sincronizados
- **Selector de Períodos Dinámico** - Agrupado por año con optgroups

### 🔧 Mejorado
- Vista de metadata con filtros y búsqueda avanzada
- Stats de calidad en tiempo real (endpoint optimizado)
- Performance de carga de períodos (<50ms)

### 🐛 Corregido
- Bugfix crítico: Sincronización de selectores de período
- Bugfix: Safe mode en categorización (protección contra duplicados)

### 📚 Documentación
- `BUGFIX_SINCRONIZACION_SELECTORES.md`
- `FEATURE_PANEL_CALIDAD_CONFIANZA.md`
- `FEATURE_APLICAR_REGLAS_MASIVO.md`
- `SELECTOR_PERIODO_DINAMICO.md`

---

## [2.0.0] - 2025-12-20

### 🚀 Agregado
- **Sistema de Insights Financieros** - 7 tipos de análisis automático
- **Exportación Excel Ejecutivo** - 5 hojas con estilos profesionales
- **Analytics Interactivos** - 3 gráficos Chart.js
- **Detección Automática de Banco** - SUPERVIELLE, GALICIA, DESCONOCIDO
- **Sistema de Reglas Aprendibles** - Mejora con uso

### 📚 Documentación
- `FEATURE_INSIGHTS_FINANCIEROS.md`
- `ETAPA7B_EXCEL_EJECUTIVO.md`
- `ETAPA5_1_DETECCION_BANCO.md`
- `ETAPA4_REGLAS_APRENDIBLES.md`

---

## [1.5.0] - 2025-12-18

### 🚀 Agregado
- **Edición Manual Completa** - Modal de edición con 37 categorías
- **Sistema de Batches** - Control de importaciones con rollback
- **Extracción de Metadata** - 8 extractores automáticos

### 📚 Documentación
- `ETAPA3_EDICION_MANUAL.md`
- `CONTROL_BATCHES_IMPLEMENTADO.md`
- `ETAPA2_IMPLEMENTACION.md`

---

## [1.0.0] - 2025-12-15

### 🚀 Agregado
- **Motor de Categorización Cascada v2.0** - 2 niveles (37 + 24 reglas)
- **Consolidación Multi-Banco** - Supervielle, Galicia
- **Reportes Ejecutivos Completos** - 5 secciones
- **Dashboard en Tiempo Real**
- **API REST** - 14 endpoints iniciales

### 📚 Documentación
- `ETAPA1_1_REGLAS_MIGRADAS.md`
- `ETAPA1_2_MOTOR_IMPLEMENTADO.md`
- `PLAN_PARIDAD_CLI.md`
- `README.md`

---

## Tipos de Cambios

- **Agregado** - Para funcionalidades nuevas
- **Mejorado** - Para cambios en funcionalidades existentes
- **Deprecado** - Para funcionalidades que se eliminarán pronto
- **Eliminado** - Para funcionalidades eliminadas
- **Corregido** - Para corrección de bugs
- **Seguridad** - En caso de vulnerabilidades

---

## Versionado

Este proyecto usa [Versionado Semántico](https://semver.org/lang/es/):

- **MAJOR** (X.0.0) - Cambios incompatibles con versiones anteriores
- **MINOR** (0.X.0) - Nuevas funcionalidades compatibles
- **PATCH** (0.0.X) - Correcciones de bugs compatibles

---

**Última actualización:** 2025-12-23
**Versión actual:** 2.4.0
