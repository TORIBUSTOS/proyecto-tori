# Quick Start: Sistema de Versionado de Catálogo

## Instalación y Setup

### 1. Migrar Base de Datos
Crear las nuevas tablas:
```bash
python backend/database/migrate_add_catalog_versioning.py
```

### 2. Ejecutar Tests
Verificar que todo funciona:
```bash
python test_catalog_upgrade.py
```

Deberías ver:
```
✓ TODOS LOS TESTS COMPLETADOS
```

### 3. Iniciar Servidor
```bash
python run_dev.py
```

## Uso Rápido (API)

### Crear Versión
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/version \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0.0",
    "descripcion": "Reorganización EGRESOS",
    "created_by": "admin"
  }'
```

### Cargar Mapeos
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

### Simular Impacto
```bash
curl -X POST http://localhost:8000/api/admin/catalogo/upgrade/simular \
  -H "Content-Type: application/json" \
  -d '{
    "from_version": "1.0.0",
    "to_version": "2.0.0"
  }'
```

### Aplicar Upgrade
```bash
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
```

## Uso Rápido (Script Python)

### Ejemplo Interactivo
```bash
python ejemplo_uso_versionado.py
```

Sigue las instrucciones del menú interactivo.

## Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/admin/catalogo/version` | POST | Crear versión |
| `/api/admin/catalogo/version` | GET | Listar versiones |
| `/api/admin/catalogo/upgrade-map` | POST | Cargar mapeos |
| `/api/admin/catalogo/upgrade/simular` | POST | Simular upgrade |
| `/api/admin/catalogo/upgrade/aplicar` | POST | Aplicar upgrade |

## Documentación Completa

Ver `SISTEMA_VERSIONADO_CATALOGO.md` para documentación detallada.

## Swagger UI

Una vez iniciado el servidor, visita:
```
http://localhost:8000/docs
```

Busca la sección **Admin Catálogo** para probar los endpoints interactivamente.

---

**IMPORTANTE**:
- Siempre simular ANTES de aplicar
- Los upgrades NO pisan categorizaciones manuales
- Todas las operaciones se registran en `audit_log`
