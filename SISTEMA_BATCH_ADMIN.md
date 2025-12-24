# Sistema de Gestión Administrativa de Batches

## Resumen Ejecutivo

Sistema administrativo para listar y eliminar batches de importación con confirmación fuerte y auditoría completa.

**Estado**: ✅ IMPLEMENTADO Y TESTEADO

⚠️ **ADVERTENCIA**: La eliminación de un batch es DEFINITIVA y borra TODOS los movimientos asociados.

## Arquitectura

### Base de Datos

Utiliza tablas existentes:

#### `import_batches` (Existente)
```sql
- id (PK)
- filename (TEXT) - nombre del archivo importado
- file_hash (TEXT) - hash único del archivo
- imported_at (TIMESTAMP) - fecha de importación
- rows_inserted (INTEGER) - filas insertadas según registro
```

#### `audit_log` (Del sistema de versionado)
```sql
- id (PK)
- actor (TEXT) - quien ejecuta
- action (TEXT) - "DELETE_BATCH"
- entity (TEXT) - "batch"
- before (JSON) - estado antes del borrado
- after (JSON) - {"deleted": true}
- created_at (TIMESTAMP)
```

### Backend

#### Core Logic (`backend/core/`)
`batch_admin.py` - Lógica de gestión de batches:
- `list_batches()` - Lista batches con estadísticas
- `delete_batch()` - Elimina batch y movimientos
- `get_batch_info()` - Info detallada de un batch

#### API Router (`backend/api/`)
`admin_batch.py` - Endpoints administrativos

### Endpoints API

Base: `/api/admin/batch`

#### GET ``
Listar todos los batches
```json
Response:
{
  "status": "success",
  "total": 10,
  "batches": [
    {
      "id": 1,
      "origen": "Movimientos_Enero.xlsx",
      "created_at": "2025-01-15T10:30:00",
      "rows_inserted": 500,
      "total_movimientos": 500
    }
  ]
}
```

#### GET `/{batch_id}`
Obtener info detallada de un batch
```json
Response:
{
  "status": "success",
  "batch": {
    "id": 1,
    "filename": "Movimientos_Enero.xlsx",
    "file_hash": "abc123...",
    "imported_at": "2025-01-15T10:30:00",
    "rows_inserted": 500,
    "total_movimientos": 500
  }
}
```

#### DELETE `/{batch_id}`
Eliminar batch y todos sus movimientos

⚠️ **OPERACIÓN DEFINITIVA - NO REVERSIBLE**

```json
Request:
{
  "confirm": true,      // OBLIGATORIO
  "actor": "admin"      // opcional
}

Response:
{
  "status": "success",
  "message": "Batch 1 eliminado exitosamente",
  "batch_id": 1,
  "origen": "Movimientos_Enero.xlsx",
  "movimientos_eliminados": 500,
  "audit_id": 42
}
```

## Reglas de Operación

### 1. Confirmación Obligatoria
```json
{
  "confirm": true  // DEBE ser true
}
```
Si `confirm != true` → Error 400

### 2. Borrado en Transacción
El proceso de eliminación:
1. Valida existencia del batch
2. Cuenta movimientos asociados
3. **Elimina movimientos** (`DELETE FROM movimientos WHERE batch_id = X`)
4. **Elimina batch** (`DELETE FROM import_batches WHERE id = X`)
5. **Registra auditoría**
6. **Commit**

Si falla cualquier paso → **ROLLBACK** completo

### 3. Auditoría Completa
Cada eliminación registra en `audit_log`:
```json
{
  "actor": "admin",
  "action": "DELETE_BATCH",
  "entity": "batch",
  "before": {
    "batch_id": 1,
    "filename": "Movimientos_Enero.xlsx",
    "file_hash": "abc123...",
    "imported_at": "2025-01-15T10:30:00",
    "rows_inserted": 500,
    "movimientos_count": 500
  },
  "after": {
    "deleted": true
  }
}
```

### 4. Sin Movimientos Huérfanos
**REGLA**: Al eliminar un batch, TODOS los movimientos asociados se eliminan.
- NO se dejan movimientos con `batch_id` inválido
- Integridad referencial garantizada

### 5. Batches Vacíos
- Permitido eliminar batches con 0 movimientos
- Útil para limpiar importaciones fallidas

## Validaciones y Seguridad

### Validaciones de Request
1. **Batch existe**: 404 si no existe
2. **Confirm = true**: 400 si no se confirma
3. **Transacción**: Rollback automático si falla

### Seguridad (Preparado para Roles)
```python
# Futuro: Proteger endpoints
# @requires_role("admin")
# @requires_role("gerencial")
```

Por ahora: Todos los endpoints son accesibles.
**TODO**: Implementar autenticación/autorización.

## Flujo de Uso

### Caso de Uso: Eliminar Importación Incorrecta

#### 1. Listar batches
```bash
GET /api/admin/batch

# Identifica el batch incorrecto
```

#### 2. Verificar batch
```bash
GET /api/admin/batch/5

# Revisa cuántos movimientos tiene
```

#### 3. Eliminar batch
```bash
DELETE /api/admin/batch/5
Body: {"confirm": true, "actor": "admin"}

# Batch y movimientos eliminados
```

#### 4. Verificar auditoría
```sql
SELECT * FROM audit_log
WHERE action = 'DELETE_BATCH'
ORDER BY created_at DESC
LIMIT 1;
```

## Testing

### Ejecutar Tests
```bash
python test_batch_admin.py
```

### Test Suite
```
✓ TEST 1: Listar batches (11 encontrados)
✓ TEST 2: Obtener info del batch
✓ TEST 4: Crear batch de prueba (3 movimientos)
✓ TEST 5: Eliminar batch con confirm
  - Movimientos antes: 3
  - Movimientos después: 0
  - Batch eliminado ✓
✓ TEST 6: Verificar auditoría (registro creado)

✓ TODOS LOS TESTS COMPLETADOS
```

## Archivos Creados/Modificados

### Core
```
backend/core/batch_admin.py          (Nuevo)
```

### API
```
backend/api/admin_batch.py           (Nuevo)
backend/api/main.py                  (Modificado - router registrado)
```

### Tests
```
test_batch_admin.py                  (Nuevo)
```

### Documentación
```
SISTEMA_BATCH_ADMIN.md               (Este archivo)
```

## Ejemplos de Uso (API)

### cURL: Listar Batches
```bash
curl -X GET http://localhost:8000/api/admin/batch
```

### cURL: Obtener Info de Batch
```bash
curl -X GET http://localhost:8000/api/admin/batch/5
```

### cURL: Eliminar Batch
```bash
curl -X DELETE http://localhost:8000/api/admin/batch/5 \
  -H "Content-Type: application/json" \
  -d '{"confirm": true, "actor": "admin"}'
```

### Python: Listar Batches
```python
import requests

response = requests.get("http://localhost:8000/api/admin/batch")
batches = response.json()["batches"]

for b in batches:
    print(f"Batch {b['id']}: {b['origen']} - {b['total_movimientos']} movimientos")
```

### Python: Eliminar Batch
```python
import requests

response = requests.delete(
    "http://localhost:8000/api/admin/batch/5",
    json={"confirm": True, "actor": "admin"}
)

if response.status_code == 200:
    result = response.json()
    print(f"Eliminados: {result['movimientos_eliminados']} movimientos")
else:
    print(f"Error: {response.text}")
```

## Integración con UI

### Pantalla Objetivo
**⚙️ Configuración → Gestión de Importaciones**

### Componentes UI (Preparación)

#### 1. Tabla de Batches
```
ID | Archivo               | Fecha Import | Movimientos | Acciones
1  | Movimientos_Ene.xlsx  | 2025-01-15   | 500         | 🗑️
2  | Movimientos_Feb.xlsx  | 2025-02-10   | 450         | 🗑️
```

#### 2. Modal de Confirmación
```
⚠️ ADVERTENCIA

¿Está seguro de eliminar el batch?

Batch: Movimientos_Ene.xlsx
Movimientos a borrar: 500

Esta operación es DEFINITIVA y NO reversible.

[Cancelar] [Confirmar Eliminación]
```

#### 3. Flujo UI
1. Usuario ve lista de batches
2. Click en 🗑️ → Abre modal
3. Usuario confirma → POST `/api/admin/batch/{id}` con `confirm=true`
4. Success → Refresh lista
5. Error → Mostrar mensaje

## Comandos SQL Útiles

### Ver Batches
```sql
SELECT
  b.id,
  b.filename,
  b.imported_at,
  b.rows_inserted,
  COUNT(m.id) as movimientos_actuales
FROM import_batches b
LEFT JOIN movimientos m ON b.id = m.batch_id
GROUP BY b.id
ORDER BY b.imported_at DESC;
```

### Ver Auditoría de Borrados
```sql
SELECT
  created_at,
  actor,
  before->>'$.batch_id' as batch_id,
  before->>'$.filename' as filename,
  before->>'$.movimientos_count' as movimientos
FROM audit_log
WHERE action = 'DELETE_BATCH'
ORDER BY created_at DESC;
```

### Verificar Integridad (No Huérfanos)
```sql
SELECT COUNT(*) as huerfanos
FROM movimientos m
LEFT JOIN import_batches b ON m.batch_id = b.id
WHERE m.batch_id IS NOT NULL
  AND b.id IS NULL;

-- Debe retornar: 0
```

## Errores Comunes y Soluciones

### Error 400: "Se requiere confirm=true"
**Solución**: Agregar `"confirm": true` en el body del request.

### Error 404: "Batch X no existe"
**Solución**: Verificar que el batch_id es correcto con GET `/api/admin/batch`.

### Error 500: Error al eliminar
**Solución**:
1. Verificar logs del servidor
2. Verificar integridad de DB
3. Rollback automático protege datos

### Movimientos huérfanos después de borrar
**NO DEBERÍA PASAR**: El sistema usa transacciones.
Si ocurre: Reportar bug.

## Cumplimiento de Especificaciones TORO

### ✅ DB: Soporte Mínimo
- Usa tabla `import_batches` existente
- Usa tabla `audit_log` del sistema de versionado
- NO crea tablas nuevas

### ✅ Backend: Servicios Core
- Módulo `batch_admin.py` con `list_batches()` y `delete_batch()`
- Borrado definitivo de movimientos asociados
- Sin movimientos huérfanos

### ✅ Endpoints Admin
- Router `/api/admin/batch`
- GET (listar), GET/{id} (detalle), DELETE/{id} (eliminar)
- Requiere `confirm: true` para DELETE

### ✅ Auditoría Obligatoria
- Registro en `audit_log` con actor, before/after
- NO log por movimiento individual (agregado)

### ✅ Seguridad y Validaciones
- Batch inexistente → 404
- confirm != true → 400
- Batch con 0 movimientos → permitido

### ✅ Integración con UI (Preparación)
- NO nueva pantalla principal
- Consumible desde ⚙️ Configuración
- Modal de confirmación fuerte (diseño preparado)

## Próximos Pasos (Opcionales)

- [ ] Implementar autenticación/roles (admin/gerencial)
- [ ] UI web para gestión visual de batches
- [ ] Export de batch antes de eliminar (backup JSON)
- [ ] Soft delete con flag `deleted_at` (alternativa)
- [ ] Restaurar batch desde auditoría (si se guarda backup)

## Notas Técnicas

### Transacciones
SQLAlchemy maneja transacciones automáticamente:
- `db.commit()` confirma cambios
- Exception → `db.rollback()` automático
- Garantiza atomicidad

### Performance
- `list_batches()` usa JOIN con COUNT agregado
- Índices en `batch_id` para joins rápidos
- Borrado en batch (no loop)

### Auditoría vs Performance
- Auditoría agregada (1 registro por batch)
- NO log por movimiento (evita N inserts)
- Balance entre trazabilidad y performance

---

**Autor**: Claude Sonnet 4.5
**Fecha**: 2025-12-24
**Versión**: 1.0.0
