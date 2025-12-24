# ETAPA 4 - REGLAS APRENDIBLES (MVP) ✅

**Estado**: COMPLETADA
**Fecha**: 2025-12-17

---

## OBJETIVO

Implementar sistema de aprendizaje simple basado en reglas:
- Usuario edita movimiento y marca "Recordar regla" → se guarda patrón en DB
- En futuras categorizaciones, las reglas aprendidas se aplican ANTES de reglas estáticas
- Sin romper ETAPA 1/2/3, sin ML, sin refactor grande

---

## ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE CATEGORIZACIÓN                   │
└─────────────────────────────────────────────────────────────┘

1. Usuario importa extractos
2. Sistema categoriza movimientos:

   ┌──────────────────────────────────────────┐
   │  PASO 1: Reglas Aprendidas (ETAPA 4)    │ ← NUEVO
   │  - Buscar patrón en descripción          │
   │  - Si matchea → aplicar y SALIR          │
   │  - Si no matchea → continuar a paso 2    │
   └──────────────────────────────────────────┘
                    ↓ (si no match)
   ┌──────────────────────────────────────────┐
   │  PASO 2: Motor Cascada (ETAPA 1/2)      │ ← EXISTENTE
   │  - Nivel 1: Reglas de Concepto          │
   │  - Nivel 2: Reglas de Refinamiento       │
   └──────────────────────────────────────────┘

3. Usuario edita movimiento en UI:
   - Cambia categoría/subcategoría
   - Marca checkbox "Recordar regla" (default: ON)
   - Sistema extrae patrón de descripción
   - Guarda regla en DB para futuros usos

4. Próxima categorización:
   - Movimientos similares se categorizan automáticamente
   - Por la regla aprendida (paso 1)
```

---

## IMPLEMENTACIÓN

### A) MODELO DE DATOS

**Archivo**: `backend/models/regla_categorizacion.py` (NUEVO)

```python
class ReglaCategorizacion(Base):
    __tablename__ = "reglas_categorizacion"

    id = Column(Integer, primary_key=True)
    patron = Column(String, unique=True, nullable=False)  # Patrón normalizado
    categoria = Column(String, nullable=False)
    subcategoria = Column(String, nullable=False)
    confianza = Column(Integer, default=50)  # 0-100
    veces_usada = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
```

**Tabla creada**: `reglas_categorizacion`

---

### B) NORMALIZACIÓN Y PATRONES

**Archivo**: `backend/core/reglas_aprendidas.py` (NUEVO)

**Funciones principales**:

1. **`normalizar_texto(texto)`**
   - Convierte a UPPERCASE
   - Remueve caracteres especiales
   - Compacta espacios múltiples

2. **`generar_patron_desde_descripcion(descripcion, max_palabras=5)`**
   - Normaliza descripción
   - Toma primeras 5 palabras
   - Retorna patrón para matching

   Ejemplo:
   ```
   Entrada:  "COMPRA VISA DEBITO COMERCIO PEDIDOSYA ENTREGA 123"
   Patrón:   "COMPRA VISA DEBITO COMERCIO PEDIDOSYA"
   ```

3. **`buscar_regla_aplicable(descripcion, db)`**
   - Normaliza descripción
   - Busca reglas cuyo patrón esté contenido en la descripción
   - Ordena por confianza DESC, veces_usada DESC
   - Retorna primera regla que matchea

4. **`aplicar_regla_a_movimiento(regla, movimiento, db)`**
   - Setea categoria/subcategoria del movimiento
   - Incrementa veces_usada de la regla
   - Incrementa confianza de la regla (+1, max 100)

5. **`obtener_o_crear_regla(patron, categoria, subcategoria, db)`**
   - Si existe regla con ese patrón:
     - Incrementa veces_usada (+1)
     - Incrementa confianza (+10, max 100)
     - Actualiza categoría/subcategoría (última corrección manda)
   - Si no existe:
     - Crea nueva regla con confianza=50, veces_usada=1

---

### C) ENDPOINTS API

**Archivo**: `backend/api/routes.py` (MODIFICADO)

#### 1. POST /api/reglas

Crea o actualiza regla aprendida.

**Request Body**:
```json
{
  "patron": "COMPRA VISA DEBITO COMERCIO",
  "categoria": "EGRESOS",
  "subcategoria": "Prestadores_Farmacias"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "mensaje": "Regla guardada exitosamente",
  "regla": {
    "id": 1,
    "patron": "COMPRA VISA DEBITO COMERCIO",
    "categoria": "EGRESOS",
    "subcategoria": "Prestadores_Farmacias",
    "confianza": 60,
    "veces_usada": 2,
    "created_at": "2025-12-17T10:30:00"
  }
}
```

#### 2. GET /api/reglas

Lista todas las reglas, ordenadas por confianza y uso.

**Query Params**:
- `categoria` (opcional): Filtrar por categoría

**Response** (200 OK):
```json
{
  "status": "success",
  "total": 5,
  "reglas": [
    {
      "id": 1,
      "patron": "COMPRA VISA DEBITO COMERCIO",
      "categoria": "EGRESOS",
      "subcategoria": "Prestadores_Farmacias",
      "confianza": 85,
      "veces_usada": 15,
      "created_at": "2025-12-17T10:30:00"
    }
  ]
}
```

---

### D) INTEGRACIÓN EN CATEGORIZACIÓN

**Archivo**: `backend/core/categorizador_cascada.py` (MODIFICADO)

**Función**: `categorizar_movimientos()`

**Cambios**:

```python
# ANTES (ETAPA 1/2)
for mov in movimientos:
    resultado = motor.categorizar_cascada(concepto, detalle, monto)
    mov.categoria = resultado.categoria
    mov.subcategoria = resultado.subcategoria

# DESPUÉS (ETAPA 4)
for mov in movimientos:
    # PASO 1: Intentar regla aprendida
    regla = buscar_regla_aplicable(mov.descripcion, db)
    if regla:
        aplicar_regla_a_movimiento(regla, mov, db)
        aplicados_regla_aprendida += 1
        continue  # ← NO pasar por motor cascada

    # PASO 2: Motor cascada (comportamiento actual)
    resultado = motor.categorizar_cascada(concepto, detalle, monto)
    mov.categoria = resultado.categoria
    mov.subcategoria = resultado.subcategoria
```

**Estadísticas nuevas**:
- `aplicados_regla_aprendida`: Contador de movimientos categorizados por reglas aprendidas
- Motor reporta: `"CategorizadorCascada v2.0 + Reglas Aprendibles (ETAPA 4)"`

---

### E) INTERFAZ DE USUARIO

#### 1. Modal de Edición

**Archivo**: `frontend/templates/index.html` (MODIFICADO)

**Cambio**:
```html
<!-- AGREGADO -->
<div class="form-group" style="margin-top: 15px;">
  <label style="display: flex; align-items: center; cursor: pointer;">
    <input id="recordar-regla" type="checkbox" checked style="margin-right: 8px;" />
    <span>Recordar esta regla (ETAPA 4)</span>
  </label>
  <small style="color: #718096;">
    Se guardará esta categorización para futuros movimientos similares
  </small>
</div>
```

**Comportamiento**:
- Checkbox viene MARCADO por defecto
- Usuario puede desmarcarlo si no quiere guardar regla

#### 2. Lógica JavaScript

**Archivo**: `frontend/static/js/app.js` (MODIFICADO)

**Función**: `guardarCambios()`

```javascript
// ETAPA 4: Si checkbox está marcado, guardar regla
if (recordarRegla && descripcion && categoria && subcategoria) {
  const patron = generarPatronDesdeDescripcion(descripcion);
  await guardarReglaAprendida(patron, categoria, subcategoria);
}
```

**Funciones nuevas agregadas**:

1. `normalizarTexto(texto)` - Normalización en JS (replica lógica Python)
2. `generarPatronDesdeDescripcion(descripcion)` - Extrae patrón (primeras 5 palabras)
3. `guardarReglaAprendida(patron, categoria, subcategoria)` - Llama POST /api/reglas

---

## TESTS

**Archivo**: `test_reglas_aprendidas.py` (NUEVO)

### Tests implementados:

1. ✅ **Test 1**: Normalización de texto
2. ✅ **Test 2**: Generación de patrones
3. ✅ **Test 3**: Crear regla en DB (primera vez)
4. ✅ **Test 4**: Actualizar regla existente (incrementa contadores)
5. ✅ **Test 5**: Buscar regla aplicable
6. ✅ **Test 6**: Categorización automática con regla aprendida
7. ✅ **Test 7**: Reglas no rompen motor cascada (fallback funciona)

### Resultado:

```
============================================================
✅ TODOS LOS TESTS PASARON
============================================================

✓ ETAPA 4 MVP - REGLAS APRENDIBLES: COMPLETADA

Tests ejecutados:
  - Normalización: OK
  - Generación patrones: OK
  - Crear regla: OK (confianza=50, veces_usada=1)
  - Actualizar regla: OK (confianza=60, veces_usada=2)
  - Buscar regla: OK
  - Categorización con regla: OK (aplicó regla aprendida)
  - Fallback a cascada: OK (motor cascada sigue funcionando)
```

---

## CRITERIO DE ACEPTACIÓN ✅

### CUMPLIDO:

1. ✅ **Desde la UI**: editar movimiento, tildar "Recordar regla", guardar
   - Checkbox implementado en modal
   - Default: CHECKED
   - Guardado integrado en función `guardarCambios()`

2. ✅ **Se crea regla en DB**
   - Tabla `reglas_categorizacion` creada
   - Modelo ReglaCategorizacion registrado
   - Endpoints POST/GET funcionando

3. ✅ **Al correr categorización, movimientos similares se categorizan automáticamente**
   - Integrado en `categorizar_movimientos()`
   - Reglas aprendidas se aplican ANTES de reglas estáticas
   - Estadística `aplicados_regla_aprendida` en respuesta

4. ✅ **Si no hay match, sistema se comporta igual que antes**
   - Test 7 valida que motor cascada sigue funcionando
   - No rompe ETAPA 1/2/3

5. ✅ **Tests pasan**
   - 7 tests ejecutados
   - Todos pasaron exitosamente

---

## FLUJO COMPLETO DE USO

### Escenario típico:

1. **Usuario importa extractos**
   ```
   Movimiento: "COMPRA VISA DEBITO COMERCIO PEDIDOSYA ENTREGA 123"
   Categoría: OTROS / Sin_Clasificar (por defecto)
   ```

2. **Usuario edita movimiento en UI**
   - Abre modal de edición
   - Cambia categoría a: EGRESOS
   - Cambia subcategoría a: Prestadores_Farmacias
   - Checkbox "Recordar regla" está MARCADO
   - Hace clic en "Guardar Cambios"

3. **Sistema guarda regla**
   ```
   Patrón generado: "COMPRA VISA DEBITO COMERCIO PEDIDOSYA"
   Categoría: EGRESOS
   Subcategoría: Prestadores_Farmacias
   Confianza: 50%
   Veces usada: 1
   ```

4. **Próxima importación**
   ```
   Movimiento nuevo: "COMPRA VISA DEBITO COMERCIO PEDIDOSYA DELIVERY 456"

   Sistema busca reglas aprendidas:
   - Encuentra patrón "COMPRA VISA DEBITO COMERCIO PEDIDOSYA"
   - Aplica automáticamente:
     - Categoría: EGRESOS
     - Subcategoría: Prestadores_Farmacias
     - Confianza: 50%
   - Incrementa: veces_usada=2, confianza=51%
   ```

5. **Usuario confirma que está correcto**
   - Si vuelve a editar y guardar con "Recordar regla":
     - Confianza sube a 61%
     - Veces usada: 3
   - Regla se vuelve más "fuerte" con el uso

---

## ARCHIVOS MODIFICADOS/CREADOS

### NUEVOS:
- ✅ `backend/models/regla_categorizacion.py` - Modelo ORM
- ✅ `backend/core/reglas_aprendidas.py` - Lógica de normalización y matching
- ✅ `test_reglas_aprendidas.py` - Suite de tests
- ✅ `ETAPA4_REGLAS_APRENDIBLES.md` - Esta documentación

### MODIFICADOS:
- ✅ `backend/models/__init__.py` - Import de ReglaCategorizacion
- ✅ `backend/database/init_db.py` - Import para crear tabla
- ✅ `backend/api/routes.py` - Endpoints POST/GET /api/reglas
- ✅ `backend/core/categorizador_cascada.py` - Integración de reglas aprendidas
- ✅ `frontend/templates/index.html` - Checkbox en modal
- ✅ `frontend/static/js/app.js` - Lógica de guardado de regla

---

## RESTRICCIONES CUMPLIDAS

✅ **NO romper ETAPA 1 ni ETAPA 2**: Motor cascada sigue intacto
✅ **NO refactor grande**: Cambios acotados, todo "encima"
✅ **NO machine learning**: Sistema basado en reglas simples
✅ **NO explorar repo**: Solo se tocaron archivos indicados
✅ **Comportamiento actual preservado**: Si no hay regla aprendida, funciona igual que antes

---

## PRÓXIMOS PASOS (FUTURO, NO MVP)

### Mejoras opcionales:
1. **Panel de administración de reglas**
   - Ver todas las reglas aprendidas
   - Editar/eliminar reglas
   - Ver estadísticas de uso

2. **Mejoras en matching**
   - Fuzzy matching
   - Stemming de palabras
   - Sinónimos

3. **Confidence decay**
   - Reducir confianza si regla no se usa por X tiempo
   - Auto-eliminar reglas obsoletas

4. **Sugerencias proactivas**
   - "Detectamos que editaste 3 movimientos similares, ¿querés crear una regla?"

5. **Export/Import de reglas**
   - Compartir reglas entre usuarios
   - Backup de reglas

---

## CONCLUSIÓN

**ETAPA 4 - REGLAS APRENDIBLES**: ✅ **COMPLETADA**

Sistema de aprendizaje simple implementado exitosamente:
- Usuario puede "enseñar" al sistema a categorizar
- Reglas aprendidas se aplican automáticamente
- No rompe funcionalidad existente
- Tests pasan al 100%
- MVP cerrado y funcional

**Resultado**: El sistema ahora aprende de las correcciones del usuario y mejora su precisión con el tiempo, sin necesidad de machine learning ni cambios complejos.
