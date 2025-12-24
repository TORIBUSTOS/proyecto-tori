# Sistema de Versionado y Upgrade de Catálogo

## Resumen Ejecutivo

Sistema de versionado de catálogo de categorías que permite migrar categorizaciones entre versiones mediante mapeos configurables, con simulación previa y auditoría completa.

**Estado**: ✅ IMPLEMENTADO Y TESTEADO

## Arquitectura

### Base de Datos

#### 1. `catalog_version`
Registro de versiones del catálogo
```sql
- id (PK)
- version (TEXT UNIQUE) - ej: "1.0.0", "2.0.0"
- descripcion (TEXT) - propósito de la versión
- created_at (TIMESTAMP)
- created_by (TEXT) - usuario creador
```

#### 2. `catalog_upgrade_map`
Mapeos de migración entre versiones
```sql
- id (PK)
- from_version (TEXT) - versión origen
- to_version (TEXT) - versión destino
- from_cat (TEXT) - categoría origen
- from_sub (TEXT) - subcategoría origen (nullable)
- to_cat (TEXT) - categoría destino
- to_sub (TEXT) - subcategoría destino (nullable)
- action (TEXT) - "RENAME"|"MOVE"|"DEACTIVATE"
- created_at (TIMESTAMP)
```

#### 3. `audit_log`
Auditoría de todas las operaciones
```sql
- id (PK)
- actor (TEXT) - quien ejecuta
- action (TEXT) - acción realizada
- entity (TEXT) - entidad afectada
- before (JSON) - estado previo
- after (JSON) - estado posterior
- created_at (TIMESTAMP)
```

### Backend

#### Modelos (`backend/models/`)
- `catalog_version.py` - ORM para versiones
- `catalog_upgrade_map.py` - ORM para mapeos
- `audit_log.py` - ORM para auditoría

#### Core Logic (`backend/core/`)
- `categorias_catalogo.py` - Extendido con `get_catalog(version)`
- `catalog_upgrade.py` - Lógica de simulación y aplicación

#### API Router (`backend/api/`)
- `admin_catalogo.py` - Endpoints de administración

### Endpoints API

Base: `/api/admin/catalogo`

#### POST `/version`
Crear nueva versión del catálogo
```json
Request:
{
  "version": "2.0.0",
  "descripcion": "Reorganización de EGRESOS",
  "created_by": "admin"
}

Response:
{
  "status": "success",
  "version_id": 1,
  "version": "2.0.0",
  "created_at": "2025-12-23T..."
}
```

#### GET `/version`
Listar todas las versiones
```json
Response:
{
  "status": "success",
  "total": 2,
  "versiones": [
    {
      "id": 1,
      "version": "1.0.0",
      "descripcion": "...",
      "created_at": "...",
      "created_by": "system"
    }
  ]
}
```

#### POST `/upgrade-map`
Cargar mapeos de upgrade (bulk)
```json
Request:
{
  "mapeos": [
    {
      "from_version": "1.0.0",
      "to_version": "2.0.0",
      "from_cat": "EGRESOS",
      "from_sub": "Prestadores_Farmacias",
      "to_cat": "EGRESOS",
      "to_sub": "Salud - Prestadores",
      "action": "RENAME"
    },
    {
      "from_version": "1.0.0",
      "to_version": "2.0.0",
      "from_cat": "EGRESOS",
      "from_sub": "Educacion_Cursos",
      "to_cat": "INVERSIONES",
      "to_sub": "Desarrollo Personal",
      "action": "MOVE"
    }
  ]
}

Response:
{
  "status": "success",
  "mapeos_creados": 2
}
```

#### POST `/upgrade/simular`
Simular impacto SIN aplicar cambios
```json
Request:
{
  "from_version": "1.0.0",
  "to_version": "2.0.0"
}

Response:
{
  "status": "success",
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "total_afectados": 1250,
  "top_mapeos": [
    {
      "from_cat": "EGRESOS",
      "from_sub": "Prestadores_Farmacias",
      "to_cat": "EGRESOS",
      "to_sub": "Salud - Prestadores",
      "action": "RENAME",
      "affected_count": 800
    }
  ]
}
```

#### POST `/upgrade/aplicar`
Aplicar upgrade real a movimientos
```json
Request:
{
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "confirm": true,
  "actor": "admin",
  "scope": {
    "batch_id": 1,           // opcional
    "fecha_desde": "2024-01-01",  // opcional
    "fecha_hasta": "2024-12-31"   // opcional
  }
}

Response:
{
  "status": "success",
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "total_procesados": 1250,
  "total_actualizados": 1100,
  "total_preservados": 150,  // manuales
  "audit_id": 42
}
```

## Reglas de Operación

### Preservación de Manuales
- **NO se pisan** categorizaciones manuales (`confianza_fuente == "manual"`)
- Se cuentan como "preservados" en el resultado

### Confianza Post-Upgrade
- `confianza_porcentaje = 90`
- `confianza_fuente = "upgrade_catalogo"`

### Scope Filtering
Soporta filtros opcionales:
- `batch_id`: Aplicar solo a un batch específico
- `fecha_desde` / `fecha_hasta`: Rango de fechas

### Auditoría
Todas las operaciones se registran en `audit_log`:
- Creación de versiones
- Carga de mapeos
- Aplicación de upgrades (con before/after agregado)

## Flujo de Uso

### 1. Crear Nueva Versión
```bash
POST /api/admin/catalogo/version
{
  "version": "2.0.0",
  "descripcion": "Reorganización categorías EGRESOS"
}
```

### 2. Definir Mapeos
```bash
POST /api/admin/catalogo/upgrade-map
{
  "mapeos": [...]
}
```

### 3. Simular Impacto
```bash
POST /api/admin/catalogo/upgrade/simular
{
  "from_version": "1.0.0",
  "to_version": "2.0.0"
}
```

### 4. Aplicar Upgrade
```bash
POST /api/admin/catalogo/upgrade/aplicar
{
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "confirm": true,
  "scope": {"batch_id": 1}
}
```

### 5. Verificar Resultados
- Consultar `audit_log` para tracking
- Revisar movimientos actualizados

## Testing

### Ejecutar Tests
```bash
python test_catalog_upgrade.py
```

### Test Suite
1. ✅ Crear versiones
2. ✅ Cargar mapeos
3. ✅ Simular upgrade
4. ✅ Aplicar upgrade
5. ✅ Verificar auditoría

## Archivos Creados

### Modelos
- `backend/models/catalog_version.py`
- `backend/models/catalog_upgrade_map.py`
- `backend/models/audit_log.py`

### Core
- `backend/core/catalog_upgrade.py`

### API
- `backend/api/admin_catalogo.py`

### Database
- `backend/database/migrate_add_catalog_versioning.py`

### Tests
- `test_catalog_upgrade.py`

## Migración de Base de Datos

Ejecutar migración para crear tablas:
```bash
python backend/database/migrate_add_catalog_versioning.py
```

O se ejecuta automáticamente al correr el test suite.

## Ejemplos de Mapeos

### RENAME: Cambiar nombre de subcategoría
```json
{
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "from_cat": "EGRESOS",
  "from_sub": "Prestadores_Farmacias",
  "to_cat": "EGRESOS",
  "to_sub": "Salud - Prestadores",
  "action": "RENAME"
}
```

### MOVE: Mover subcategoría a otra categoría
```json
{
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "from_cat": "EGRESOS",
  "from_sub": "Educacion_Cursos",
  "to_cat": "INVERSIONES",
  "to_sub": "Desarrollo Personal",
  "action": "MOVE"
}
```

### DEACTIVATE: Marcar como inactiva
```json
{
  "from_version": "1.0.0",
  "to_version": "2.0.0",
  "from_cat": "OTROS",
  "from_sub": "Categoria_Obsoleta",
  "to_cat": "OTROS",
  "to_sub": "Sin Clasificar",
  "action": "DEACTIVATE"
}
```

## Notas Técnicas

### Versionado Lógico
- El JSON de catálogo (`categorias.json`) NO se modifica
- El versionado es **lógico**: metadata en DB + mapeos
- `get_catalog(version)` retorna baseline + metadato de versión

### Performance
- Simulación: Solo cuenta (`COUNT(*)`) sin modificar datos
- Aplicación: Batch updates con commit único
- Scope filtering para operaciones incrementales

### Seguridad
- Requiere `confirm=true` para aplicar cambios
- Auditoría completa de todas las operaciones
- Actor tracking en cada operación

## Próximos Pasos (Opcional)

- [ ] UI web para gestión de versiones y mapeos
- [ ] Rollback de upgrades (revertir a versión anterior)
- [ ] Preview de cambios antes de aplicar
- [ ] Exportar/importar mapeos en JSON
- [ ] Validación de mapeos (verificar que existan categorías destino)

---

**Autor**: Claude Sonnet 4.5
**Fecha**: 2025-12-23
**Versión**: 1.0.0
