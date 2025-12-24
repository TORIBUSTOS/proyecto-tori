# Comandos Útiles - Sistema de Versionado de Catálogo

## Comandos Python

### Migrar Base de Datos
```bash
python backend/database/migrate_add_catalog_versioning.py
```

### Ejecutar Tests
```bash
python test_catalog_upgrade.py
```

### Ejemplo Interactivo
```bash
python ejemplo_uso_versionado.py
```

### Iniciar Servidor
```bash
# Desarrollo
python run_dev.py

# Producción
python run_prod.py
```

---

## Comandos CURL (API)

### 1. Crear Versión
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/version \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0.0",
    "descripcion": "Reorganización de categorías EGRESOS",
    "created_by": "admin"
  }'
```

### 2. Listar Versiones
```bash
curl -X GET http://localhost:8000/api/admin/catalogo/version
```

### 3. Cargar Mapeos (Ejemplo Simple)
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade-map \
  -H "Content-Type: application/json" \
  -d '{
    "mapeos": [
      {
        "from_version": "1.0.0",
        "to_version": "2.0.0",
        "from_cat": "EGRESOS",
        "from_sub": "Prestadores_Farmacias",
        "to_cat": "EGRESOS",
        "to_sub": "Salud - Prestadores",
        "action": "RENAME"
      }
    ]
  }'
```

### 4. Simular Upgrade
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/simular \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0"
  }'
```

### 5. Aplicar Upgrade (Con Scope)
```bash
# Solo batch 1
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/aplicar \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0",
    "confirm": true,
    "actor": "admin",
    "scope": {
      "batch_id": 1
    }
  }'

# Rango de fechas
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/aplicar \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0",
    "confirm": true,
    "actor": "admin",
    "scope": {
      "fecha_desde": "2024-01-01",
      "fecha_hasta": "2024-12-31"
    }
  }'

# Global (sin scope)
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/aplicar \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0",
    "confirm": true,
    "actor": "admin"
  }'
```

---

## Comandos SQL (Consultas Útiles)

### Ver Versiones Creadas
```sql
SELECT * FROM catalog_version ORDER BY created_at DESC;
```

### Ver Mapeos de un Upgrade
```sql
SELECT
  from_cat,
  from_sub,
  to_cat,
  to_sub,
  action
FROM catalog_upgrade_map
WHERE from_version = '1.0.0'
  AND to_version = '2.0.0';
```

### Ver Auditoría Reciente
```sql
SELECT
  created_at,
  actor,
  action,
  entity,
  after
FROM audit_log
ORDER BY created_at DESC
LIMIT 10;
```

### Contar Movimientos por Categoría
```sql
SELECT
  categoria,
  subcategoria,
  COUNT(*) as total,
  confianza_fuente
FROM movimientos
WHERE categoria = 'EGRESOS'
GROUP BY categoria, subcategoria, confianza_fuente
ORDER BY total DESC;
```

### Ver Movimientos Actualizados por Upgrade
```sql
SELECT
  id,
  fecha,
  descripcion,
  categoria,
  subcategoria,
  confianza_porcentaje,
  confianza_fuente
FROM movimientos
WHERE confianza_fuente = 'upgrade_catalogo'
ORDER BY fecha DESC
LIMIT 20;
```

---

## Flujo de Trabajo Típico

### Escenario: Reorganizar Categorías EGRESOS

#### 1. Planificación
```bash
# Analizar categorías actuales
sqlite3 backend/data/toro_db.sqlite "
SELECT categoria, subcategoria, COUNT(*) as total
FROM movimientos
WHERE categoria = 'EGRESOS'
GROUP BY categoria, subcategoria
ORDER BY total DESC;
"
```

#### 2. Crear Versión
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/version \
  -H "Content-Type: application/json" \
  -d '{"version": "2.0.0", "descripcion": "Reorganización EGRESOS", "created_by": "admin"}'
```

#### 3. Definir Mapeos
Crear archivo `mapeos_v2.json`:
```json
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
    }
  ]
}
```

Cargar:
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade-map \
  -H "Content-Type: application/json" \
  -d @mapeos_v2.json
```

#### 4. Simular
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/simular \
  -H "Content-Type: application/json" \
  -d '{"from_version": "1.0.0", "to_version": "2.0.0"}' | jq
```

#### 5. Revisar Simulación
Analizar el output y decidir si proceder.

#### 6. Aplicar en Test (1 Batch)
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/aplicar \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0",
    "confirm": true,
    "actor": "admin",
    "scope": {"batch_id": 1}
  }' | jq
```

#### 7. Verificar Resultados
```bash
sqlite3 backend/data/toro_db.sqlite "
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 1;
"
```

#### 8. Aplicar Global (si OK)
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/aplicar \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0",
    "confirm": true,
    "actor": "admin"
  }' | jq
```

---

## Tips y Trucos

### Formatear JSON con jq
```bash
curl ... | jq
```

### Guardar Respuesta en Archivo
```bash
curl ... > resultado.json
```

### Ver Logs en Tiempo Real
```bash
tail -f logs/toro.log
```

### Backup de DB Antes de Upgrade
```bash
cp backend/data/toro_db.sqlite backend/data/toro_db.sqlite.backup
```

### Restaurar desde Backup
```bash
cp backend/data/toro_db.sqlite.backup backend/data/toro_db.sqlite
```

---

## Troubleshooting

### Error: "No hay mapeos definidos"
```bash
# Verificar que los mapeos existen
curl -X GET http://localhost:8000/api/admin/catalogo/version
```

### Error: "confirm=true requerido"
Agregar `"confirm": true` en el request de aplicar.

### Movimientos no se actualizan
- Verificar que las categorías coincidan exactamente
- Verificar que no sean manuales (confianza_fuente != "manual")
- Verificar scope (batch_id, fechas)

### Ver Última Auditoría
```bash
sqlite3 backend/data/toro_db.sqlite "
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 1;
" | jq
```

---

## Recursos

- Documentación: `SISTEMA_VERSIONADO_CATALOGO.md`
- Quick Start: `VERSIONADO_QUICKSTART.md`
- Tests: `python test_catalog_upgrade.py`
- Swagger UI: `http://localhost:8000/docs`
