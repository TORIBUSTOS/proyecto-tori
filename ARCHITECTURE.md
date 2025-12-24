# 🏗️ TORO Investment Manager - Arquitectura del Sistema

**Versión:** 2.1.0
**Última actualización:** 2025-12-22

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Backend - Estructura](#backend---estructura)
4. [Frontend - Estructura](#frontend---estructura)
5. [Base de Datos](#base-de-datos)
6. [Flujo de Datos](#flujo-de-datos)
7. [Endpoints Principales](#endpoints-principales)
8. [Componentes Clave](#componentes-clave)
9. [Testing](#testing)
10. [Deploy y Producción](#deploy-y-producción)

---

## Visión General

TORO es un sistema web de gestión financiera con arquitectura **cliente-servidor** tradicional:

```
┌─────────────────┐         HTTP/JSON          ┌──────────────────┐
│                 │  ◄─────────────────────►   │                  │
│   FRONTEND      │                            │     BACKEND      │
│   (Vanilla JS)  │    API REST (FastAPI)      │   (Python 3.12)  │
│                 │                            │                  │
└─────────────────┘                            └──────────────────┘
                                                        │
                                                        │
                                                        ▼
                                               ┌──────────────────┐
                                               │   SQLite DB      │
                                               │   (toro.db)      │
                                               └──────────────────┘
```

**Características:**
- **Sin frameworks JS:** Vanilla JavaScript puro (ES6+)
- **SSR básico:** Templates HTML servidos por FastAPI
- **API REST:** 23 endpoints JSON
- **SPA parcial:** Navegación con fetch() sin recargas

---

## Arquitectura de Alto Nivel

### Capas del Sistema

```
┌──────────────────────────────────────────────────────────────┐
│                       PRESENTACIÓN                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │Dashboard │  │ Reportes │  │Analytics │  │ Metadata │    │
│  │  .html   │  │  .html   │  │  .html   │  │  .html   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      API REST (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  routes.py - 23 endpoints                            │   │
│  │  - Consolidación, Categorización, Reportes           │   │
│  │  - Analytics, Metadata, Batches, Edición             │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    LÓGICA DE NEGOCIO (Core)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ consolidar   │  │ categorizar  │  │  reportes    │      │
│  │    .py       │  │   _cascada   │  │    .py       │      │
│  │              │  │    .py       │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ extractores  │  │   insights   │  │   batches    │      │
│  │    .py       │  │     .py      │  │     .py      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    PERSISTENCIA (SQLAlchemy)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Movimiento  │  │ ImportBatch  │  │ReglaCateg.   │      │
│  │   (model)    │  │   (model)    │  │   (model)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   SQLite DB      │
                   │   (toro.db)      │
                   └──────────────────┘
```

---

## Backend - Estructura

### Directorio `backend/`

```
backend/
├── api/                          # Capa de API REST
│   ├── main.py                   # FastAPI app + CORS + static files
│   ├── routes.py                 # 23 endpoints (1,400 líneas)
│   └── exportacion.py            # Excel/PDF export
│
├── core/                         # Lógica de negocio
│   ├── consolidar.py             # Consolidación de extractos Excel
│   ├── categorizador_cascada.py  # Motor 2 niveles (37+24 reglas)
│   ├── extractores.py            # 8 extractores de metadata
│   ├── reportes.py               # Generación de reportes ejecutivos
│   ├── insights.py               # 7 tipos de insights financieros
│   ├── batches.py                # Control de batches con rollback
│   ├── deteccion_banco.py        # Detección automática banco
│   └── reglas_aprendidas.py      # Sistema de aprendizaje
│
├── database/
│   ├── connection.py             # SQLAlchemy engine + session
│   └── migrate_*.py              # Scripts de migración manual
│
├── models/                       # Modelos SQLAlchemy
│   ├── movimiento.py             # Modelo principal (22 columnas)
│   ├── import_batch.py           # Control de importaciones
│   └── regla_categorizacion.py  # Reglas dinámicas aprendibles
│
├── data/                         # Reglas estáticas (JSON)
│   ├── reglas_concepto.json      # 37 reglas nivel 1
│   ├── reglas_refinamiento.json  # 24 patrones nivel 2
│   └── subcategorias_disponibles.json
│
└── utils/
    └── normalizacion.py          # Utilidades de texto
```

### Tecnologías Backend

| Componente | Tecnología | Versión | Uso |
|------------|-----------|---------|-----|
| Framework | FastAPI | 0.110+ | API REST + SSR templates |
| ORM | SQLAlchemy | 2.0+ | Modelos y queries |
| Validación | Pydantic | 2.5+ | Schemas API |
| Excel | Pandas + OpenPyXL | Latest | Lectura/escritura Excel |
| Servidor | Uvicorn | 0.27+ | ASGI server |

---

## Frontend - Estructura

### Directorio `frontend/`

```
frontend/
├── templates/                  # HTML templates (SSR)
│   ├── index.html             # Dashboard (350 líneas)
│   ├── reportes.html          # Reportes ejecutivos (400 líneas)
│   ├── analytics.html         # Gráficos + insights (600 líneas)
│   ├── batches.html           # Gestión de batches (300 líneas)
│   └── metadata.html          # Explorador metadata (1,350 líneas) ★
│
└── static/
    ├── css/
    │   ├── styles.css         # Estilos globales (dark mode)
    │   └── header.css         # Navbar + breadcrumbs
    │
    ├── js/
    │   ├── app.js             # Lógica dashboard (500 líneas)
    │   ├── charts.js          # Chart.js + insights (400 líneas)
    │   └── periodo-global.js  # Sincronización período (150 líneas)
    │
    └── img/
        └── logo.svg           # Logo TORO
```

### Tecnologías Frontend

| Componente | Tecnología | Versión | Uso |
|------------|-----------|---------|-----|
| JavaScript | Vanilla ES6+ | - | Lógica cliente (sin frameworks) |
| Gráficos | Chart.js | 4.4+ | Visualizaciones interactivas |
| Estilos | CSS3 Custom Props | - | Dark mode nativo |
| HTTP Client | Fetch API | Nativa | Llamadas AJAX |
| Módulos | Inline `<script>` | - | Sin bundler |

**Filosofía:** No frameworks, máximo control, carga rápida.

---

## Base de Datos

### SQLite Schema

**Archivo:** `toro.db` (SQLite 3)

#### Tabla: `movimientos` (Principal)

| Columna | Tipo | Descripción | Index |
|---------|------|-------------|-------|
| `id` | INTEGER | PK autoincremental | PK |
| `fecha` | DATE | Fecha del movimiento | ✓ |
| `descripcion` | TEXT | Descripción bancaria | - |
| `monto` | FLOAT | Monto (positivo=ingreso, negativo=egreso) | - |
| `saldo` | FLOAT | Saldo después del movimiento | - |
| `categoria` | VARCHAR | INGRESOS, EGRESOS, etc. | ✓ |
| `subcategoria` | VARCHAR | Detalle de categoría | ✓ |
| `confianza_porcentaje` | INTEGER | 0-100% | - |
| `batch_id` | INTEGER | FK a import_batches | ✓ |
| **Metadata (8 campos):** |
| `persona_nombre` | VARCHAR | Nombre extraído | - |
| `documento` | VARCHAR | CUIT/CUIL/DNI | ✓ |
| `es_debin` | BOOLEAN | ¿Es DEBIN? | ✓ |
| `debin_id` | VARCHAR | ID del DEBIN | - |
| `cbu` | VARCHAR | CBU | - |
| `comercio` | VARCHAR | Nombre comercio | - |
| `terminal` | VARCHAR | Terminal POS | - |
| `referencia` | VARCHAR | Referencia operación | - |

**Índices:**
- `ix_movimientos_fecha`
- `ix_movimientos_categoria`
- `ix_movimientos_subcategoria`
- `ix_movimientos_batch_id`
- `ix_movimientos_documento`
- `ix_movimientos_es_debin`

#### Tabla: `import_batches`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER | PK autoincremental |
| `fecha_importacion` | DATETIME | Timestamp de carga |
| `archivo_original` | VARCHAR | Nombre del Excel |
| `total_movimientos` | INTEGER | Cantidad importada |
| `banco` | VARCHAR | SUPERVIELLE, GALICIA, etc. |
| `anulado` | BOOLEAN | ¿Rollback aplicado? |
| `fecha_anulacion` | DATETIME | Cuando se anuló |

#### Tabla: `reglas_categorizacion`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER | PK autoincremental |
| `patron_descripcion` | VARCHAR | Patrón normalizado |
| `categoria` | VARCHAR | Categoría aprendida |
| `subcategoria` | VARCHAR | Subcategoría aprendida |
| `confianza` | INTEGER | 0-100% |
| `creado_en` | DATETIME | Timestamp |

---

## Flujo de Datos

### 1. Flujo de Importación (Proceso Completo)

```
┌─────────────┐
│   Usuario   │
│  sube .xlsx │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ POST /api/proceso-   │
│       completo       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 1. consolidar.py     │  ← Lee Excel, detecta banco
│    ├─ Parsear Excel  │
│    ├─ Detectar banco │
│    └─ Crear batch    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 2. extractores.py    │  ← Extrae metadata (8 tipos)
│    ├─ Nombres        │
│    ├─ CUIT/CUIL      │
│    ├─ DEBIN          │
│    └─ CBU/Terminal   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 3. categorizador_    │  ← Categoriza (reglas + cascada)
│    cascada.py        │
│    ├─ Reglas aprend. │
│    ├─ Nivel 1 (37)   │
│    └─ Nivel 2 (24)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 4. Guardar en DB     │  ← SQLAlchemy commit
│    (movimientos)     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 5. reportes.py       │  ← Genera reporte ejecutivo
│    generar_reporte_  │
│    ejecutivo()       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  JSON Response       │
│  + Recarga frontend  │
└──────────────────────┘
```

### 2. Flujo de Consulta (Dashboard/Analytics)

```
Usuario selecciona período (navbar)
       │
       ▼
JS dispara evento 'periodoChanged'
       │
       ▼
Todas las vistas escuchan y recargan
       │
       ├─► GET /api/dashboard?mes=2025-12
       ├─► GET /api/analytics/pie-ingresos?mes=2025-12
       ├─► GET /api/analytics/pie-egresos?mes=2025-12
       └─► GET /api/analytics/flujo-diario?mes=2025-12
       │
       ▼
Backend filtra por fecha (SQLAlchemy)
       │
       ▼
JSON Response → JS renderiza
```

### 3. Flujo de Edición Manual

```
Usuario click en "Editar" (metadata o dashboard)
       │
       ▼
JS abre modal con datos actuales
       │
       ▼
Usuario cambia categoría/subcategoría
       │
       ▼
[✓] Checkbox "Recordar regla" activado
       │
       ▼
PUT /api/movimientos/{id}?categoria=X&subcategoria=Y
       │
       ├─► Actualiza movimiento en DB
       │
       └─► POST /api/reglas (si checkbox activo)
           └─► Crea regla aprendible
       │
       ▼
Frontend recarga tabla + stats
```

---

## Endpoints Principales

### Consolidación y Categorización

| Endpoint | Método | Descripción | Tiempo |
|----------|--------|-------------|--------|
| `/api/consolidar` | POST | Importar Excel + crear batch | ~2s |
| `/api/categorizar` | POST | Categorizar movimientos sin cat. | ~1s |
| `/api/proceso-completo` | POST | Pipeline completo (todo-en-uno) | ~3s |

### Consulta y Reportes

| Endpoint | Método | Descripción | Cache |
|----------|--------|-------------|-------|
| `/api/dashboard?mes=` | GET | KPIs + últimos movimientos | No |
| `/api/reportes?mes=` | GET | Reporte ejecutivo completo | Sí |
| `/api/analytics/pie-ingresos?mes=` | GET | Gráfico torta ingresos | Sí |
| `/api/metadata?mes=&q=` | GET | Metadata + stats calidad | No |

### Edición y Aprendizaje

| Endpoint | Método | Descripción | Side Effect |
|----------|--------|-------------|-------------|
| `PUT /api/movimientos/{id}` | PUT | Editar movimiento | Posible regla aprendida |
| `POST /api/reglas` | POST | Crear regla manualmente | Mejora categorización |
| `POST /api/reglas/aplicar` | POST | Recategorizar masivo | Actualiza N movimientos |

---

## Componentes Clave

### 1. Motor de Categorización Cascada

**Archivo:** `backend/core/categorizador_cascada.py`

**Funcionamiento:**
```python
def categorizar_cascada(concepto: str, detalle: str, monto: float):
    # PASO 1: Buscar en reglas aprendidas (prioridad máxima)
    regla = buscar_regla_aplicable(concepto)
    if regla:
        return aplicar_regla(regla)

    # PASO 2: Nivel 1 - Categorización por concepto (37 reglas)
    categoria, subcategoria = categorizar_nivel1(concepto)

    # PASO 3: Nivel 2 - Refinamiento por detalle (24 patrones)
    subcategoria_refinada = refinar_nivel2(detalle, subcategoria)

    return ResultadoCategorizacion(
        categoria=categoria,
        subcategoria=subcategoria_refinada or subcategoria,
        confianza=calcular_confianza()
    )
```

**Precisión:** 99%+ (mejora con reglas aprendidas)

### 2. Extracción de Metadata

**Archivo:** `backend/core/extractores.py`

**8 Extractores:**
1. `extraer_nombre()` - Nombres de personas/entidades
2. `extraer_documento()` - CUIT/CUIL/DNI (11 dígitos)
3. `extraer_debin()` - Detecta DEBIN + ID
4. `extraer_cbu()` - CBU (22 dígitos)
5. `extraer_comercio()` - Nombre del comercio
6. `extraer_terminal()` - Terminal POS
7. `extraer_referencia()` - Número de referencia
8. `extraer_importe()` - Importes secundarios

**Uso:**
```python
metadata = extraer_metadata_completa(descripcion)
# Retorna dict con 8 campos
```

### 3. Panel de Calidad (NUEVO v2.1.0)

**Ubicación:** `/metadata` (abajo de filtros)

**Métricas calculadas:**
```python
stats = {
    'confianza_promedio': 68.5,      # Promedio de confianza
    'sin_confianza_count': 12,       # Con NULL
    'confianza_cero_count': 35,      # Con 0%
    'confianza_baja_count': 58,      # Entre 1-49%
    'total_filtrado': 245
}
```

**Lógica de color coding:**
```javascript
function getQualityClass(stats) {
    // 🔴 CRÍTICO
    if (promedio < 50 || pctCero >= 15%) return 'quality-bad';

    // 🟡 ATENCIÓN
    if (promedio < 80 || pctBaja >= 20%) return 'quality-warning';

    // 🟢 OK
    return 'quality-good';
}
```

**UI:** Dark mode con alto contraste (#0f172a base, bordes de color)

### 4. Sincronización de Período

**Archivo:** `frontend/static/js/periodo-global.js`

**Funcionamiento:**
```javascript
// Objeto global singleton
window.PeriodoGlobal = {
    periodo: null,

    setPeriodo(nuevoPeriodo) {
        this.periodo = nuevoPeriodo;
        // Actualiza navbar
        // Actualiza localStorage
        // Dispara evento 'periodoChanged'
        window.dispatchEvent(new Event('periodoChanged'));
    },

    getPeriodo() {
        return this.periodo || this.leerDelDOM();
    }
};

// Cada vista escucha
window.addEventListener('periodoChanged', () => {
    cargarDatos();  // Recarga con nuevo período
});
```

**Beneficio:** Cambio en navbar → todas las vistas se sincronizan automáticamente

---

## Testing

### Backend Tests

```bash
# Tests de categorización
python test_categorizacion_dataset.py     # 37 reglas nivel 1
python test_etapa2_core.py                # Extractores metadata

# Tests de integración
python test_proceso_completo.py           # Pipeline completo
python test_analytics.py                  # Gráficos + insights

# Tests de calidad
python test_saldos_fix.py                 # Paridad saldos ($0.00)
python test_aplicar_reglas.py             # Recategorización masiva (NUEVO)
```

### Frontend Tests

```bash
# Sincronización de selectores (browser)
http://localhost:8000/test_sincronizacion_selectores.html

# Manual testing checklist
- Edición desde metadata (✏️ icon)
- Panel de calidad cambia con filtros
- Aplicar reglas masivo funciona
- Navegación dashboard ↔ metadata recarga correctamente
```

---

## Deploy y Producción

### Opción 1: Desarrollo

```bash
# Script batch (Windows)
INICIAR_TORO_DEV.bat

# O Python directo
python run_dev.py
```

**Características:**
- Auto-reload (--reload)
- Debug mode ON
- Host: 0.0.0.0:8000

### Opción 2: Producción

```bash
# Script batch (Windows)
INICIAR_TORO_PROD.bat

# O Uvicorn manual
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Características:**
- Sin auto-reload
- 4 workers
- Debug mode OFF
- Logging a archivo

### Consideraciones Producción

1. **Base de Datos**
   - SQLite OK para <100K movimientos
   - Para más: migrar a PostgreSQL

2. **Reverse Proxy**
   - Nginx recomendado
   - HTTPS con Let's Encrypt

3. **Archivos Estáticos**
   - Servir con nginx (más rápido que FastAPI)
   - Configurar cache headers

4. **Monitoring**
   - Usar `/health` endpoint
   - Logs en `logs/toro.log`

---

## Patrones de Diseño

### Backend

| Patrón | Uso | Ubicación |
|--------|-----|-----------|
| **Repository** | Acceso a datos | `models/*.py` |
| **Service Layer** | Lógica negocio | `core/*.py` |
| **Factory** | Creación de extractores | `extractores.py` |
| **Strategy** | Categorización multi-nivel | `categorizador_cascada.py` |

### Frontend

| Patrón | Uso | Ubicación |
|--------|-----|-----------|
| **Singleton** | PeriodoGlobal | `periodo-global.js` |
| **Observer** | Event listeners | Todos los `.html` |
| **Module** | Encapsulación | Cada `<script>` |

---

## Diagrama de Componentes

```
┌────────────────────────────────────────────────────────┐
│                      FRONTEND                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │Dashboard │  │Analytics │  │ Metadata │  ...       │
│  │  View    │  │   View   │  │   View   │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │              │                   │
│       └─────────────┼──────────────┘                   │
│                     │                                  │
│            ┌────────▼────────┐                         │
│            │ periodo-global  │  (Sincronización)       │
│            │      .js        │                         │
│            └────────┬────────┘                         │
└─────────────────────┼───────────────────────────────────┘
                      │ Fetch API
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  BACKEND (FastAPI)                      │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │           routes.py (23 endpoints)         │         │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │         │
│  │  │Consolid. │  │ Reportes │  │  Batch   │ │         │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘ │         │
│  └───────┼─────────────┼─────────────┼────────┘         │
│          │             │             │                  │
│  ┌───────▼─────────────▼─────────────▼────────┐         │
│  │            CORE (Lógica Negocio)           │         │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │         │
│  │  │consolidar│  │categorizar│  │ reportes │ │         │
│  │  │   .py    │  │  _cascada │  │   .py    │ │         │
│  │  └──────────┘  │    .py    │  └──────────┘ │         │
│  │                └──────────┘                 │         │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │         │
│  │  │extractor │  │ insights │  │ batches  │ │         │
│  │  │   .py    │  │   .py    │  │   .py    │ │         │
│  │  └──────────┘  └──────────┘  └──────────┘ │         │
│  └────────────────────┬─────────────────────┘           │
│                       │                                 │
│  ┌────────────────────▼─────────────────────┐           │
│  │         MODELS (SQLAlchemy)              │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐│           │
│  │  │Movimiento│  │ImportBatch│  │ReglaCateg││           │
│  │  └──────────┘  └──────────┘  └──────────┘│           │
│  └────────────────────┬─────────────────────┘           │
└───────────────────────┼─────────────────────────────────┘
                        │
                        ▼
               ┌──────────────┐
               │   toro.db    │
               │   (SQLite)   │
               └──────────────┘
```

---

## Conclusión

TORO Investment Manager es un sistema **monolítico modular** con:

- **Backend Python:** FastAPI + SQLAlchemy + Pandas
- **Frontend Vanilla JS:** Sin frameworks, máxima performance
- **Base de Datos SQLite:** Simple y eficaz
- **Arquitectura en capas:** Presentación → API → Negocio → Datos

**Ventajas:**
- ✅ Fácil de entender
- ✅ Fácil de mantener
- ✅ Rápido de deployar
- ✅ Sin dependencias complejas

**Ideal para:** Equipos pequeños, deploys rápidos, control total del código.

---

**Autor:** Claude Code
**Versión:** 2.1.0
**Fecha:** 2025-12-22
