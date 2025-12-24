# 🎯 PLAN DE PARIDAD: CLI → WEB
## TORO Investment Manager - Roadmap hacia Paridad Funcional

**Fecha:** 16 de Diciembre 2024
**Objetivo:** Llevar la versión WEB al mismo nivel funcional que el sistema CLI v2.0.0

---

## 📊 ANÁLISIS COMPARATIVO: CLI vs WEB

### ✅ FUNCIONALIDADES YA IMPLEMENTADAS EN WEB

| Funcionalidad | CLI v2.0 | WEB v2.0 | Estado |
|--------------|----------|----------|---------|
| **Consolidación Multi-Banco** | ✅ Supervielle + Galicia | ✅ Normalización de columnas | ✅ COMPLETO |
| **Normalización Flexible** | ✅ Sin tildes, case-insensitive | ✅ `_norm_col()` implementado | ✅ COMPLETO |
| **Categorización Básica** | ✅ 6 categorías con keywords | ✅ 6 categorías con keywords | ✅ COMPLETO |
| **Reportes Ejecutivos** | ✅ KPIs + Top Egresos | ✅ KPIs + Top Egresos | ✅ COMPLETO |
| **Dashboard Web** | ❌ No tiene (es CLI) | ✅ Dashboard en tiempo real | ✅ MEJOR |
| **Gestión de Batches** | ❌ No tiene | ✅ Sistema completo | ✅ MEJOR |
| **API REST** | ❌ No tiene | ✅ 7 endpoints FastAPI | ✅ MEJOR |
| **Proceso Completo** | ✅ `--consolidar --categorizar --reportes` | ✅ POST /api/proceso-completo | ✅ COMPLETO |

### ❌ FUNCIONALIDADES FALTANTES EN WEB (PRESENTES EN CLI)

| # | Funcionalidad CLI | Estado WEB | Prioridad |
|---|-------------------|------------|-----------|
| 1 | **Categorizador Cascada v2.0** (2 niveles: Concepto → Detalle) | ❌ Solo 1 nivel básico | 🔴 CRÍTICA |
| 2 | **37 reglas de categorización** | ❌ Solo 6 categorías | 🔴 CRÍTICA |
| 3 | **Extracción de metadata** (nombres, CUIT, DEBIN) | ❌ No implementado | 🔴 CRÍTICA |
| 4 | **Sistema de aprendizaje** (reglas.json) | ❌ No implementado | 🟡 MEDIA |
| 5 | **Corrección manual interactiva** | ❌ No hay UI de edición | 🔴 CRÍTICA |
| 6 | **Detección automática de banco** (por estructura) | ⚠️ Normalización genérica | 🟡 MEDIA |
| 7 | **Gráficos interactivos** (Chart.js) | ❌ Solo tablas | 🟡 MEDIA |
| 8 | **Reporte Excel ejecutivo** (5 hojas) | ❌ Solo JSON | 🟡 MEDIA |
| 9 | **Top Prestadores** | ❌ Solo top egresos por categoría | 🟢 BAJA |
| 10 | **Flujo de caja diario** (gráfico línea) | ❌ No implementado | 🟢 BAJA |
| 11 | **Selección de archivos específicos** | ❌ Procesa todo | 🟢 BAJA |
| 12 | **Sistema de sesión de trabajo** | ⚠️ Batches cumplen función similar | ✅ OK |

---

## 🚀 PLAN DE IMPLEMENTACIÓN POR PRIORIDAD

### 🔴 FASE 1: FUNCIONALIDADES CRÍTICAS (2-3 semanas)

#### 1.1 Categorizador Cascada v2.0 ⭐⭐⭐
**Objetivo:** Implementar sistema de categorización de 2 niveles

**Estado CLI:**
- 37 reglas de nivel 1 (keywords de concepto)
- 24 patrones de refinamiento (nivel 2 en detalle)
- 99%+ de cobertura automática
- Estructura: INGRESOS (3 subcategorías), EGRESOS (6 subcategorías)

**Tareas:**
- [ ] **Migrar estructura de categorías del CLI**
  ```python
  # backend/core/categorias.py
  CATEGORIAS = {
      "INGRESOS": {
          "Afiliados_DEBIN": [...],
          "Pacientes_Transferencia": [...],
          "Otros_Ingresos": [...]
      },
      "EGRESOS": {
          "Prestadores": [...],
          "Sueldos": [...],
          "Impuestos": [...],
          "Comisiones_Bancarias": [...],
          "Servicios": [...],
          "Gastos_Operativos": [...]
      }
  }
  ```

- [ ] **Implementar lógica de 2 niveles**
  ```python
  def categorizar_cascada(concepto: str, detalle: str, monto: float):
      # Nivel 1: Concepto (INGRESOS/EGRESOS + subcategoría)
      categoria, subcategoria = categorizar_nivel1(concepto)

      # Nivel 2: Refinamiento basado en detalle
      subcategoria_refinada = refinar_nivel2(detalle, subcategoria)

      return categoria, subcategoria_refinada
  ```

- [ ] **Actualizar modelo Movimiento**
  ```python
  # backend/models/movimiento.py
  subcategoria = Column(String, nullable=True, index=True)
  confianza_porcentaje = Column(Integer, default=0)  # 0-100
  ```

- [ ] **Migrar las 37 reglas del CLI**
  - Crear archivo `backend/data/reglas_cascada.json`
  - Importar todas las reglas del CLI
  - Adaptar formato si es necesario

**Archivos afectados:**
- `backend/core/categorizar.py` (reescritura completa)
- `backend/models/movimiento.py` (agregar columna)
- `backend/data/reglas_cascada.json` (nuevo)
- `backend/api/routes.py` (actualizar response)

**Tiempo estimado:** 5-7 días

---

#### 1.2 Extracción de Metadata ⭐⭐⭐
**Objetivo:** Extraer nombres, CUIT, DEBIN de los movimientos

**Estado CLI:**
```python
# El CLI extrae:
- Persona_Nombre: "HECTOR GASTON OLMEDO"
- Documento: "20336991898" (CUIT/CUIL/DNI)
- Es_DEBIN: True/False
- DEBIN_ID: "12345"
```

**Tareas:**
- [ ] **Implementar extractores**
  ```python
  # backend/core/extractores.py

  import re

  def extraer_nombre(detalle: str) -> str | None:
      # Patrón: palabras en mayúsculas seguidas de DOCUMENTO/CUIT
      patron = r"([A-Z\s]+)(?:\s+DOCUMENTO|\s+CUIT)"
      match = re.search(patron, detalle)
      return match.group(1).strip() if match else None

  def extraer_documento(detalle: str) -> str | None:
      # Patrón: secuencia de 8-11 dígitos después de DOCUMENTO/CUIT
      patron = r"(?:DOCUMENTO|CUIT)[:\s]*(\d{8,11})"
      match = re.search(patron, detalle)
      return match.group(1) if match else None

  def es_debin(concepto: str, detalle: str) -> bool:
      return "DEBIN" in concepto.upper() or "DEBIN" in detalle.upper()

  def extraer_debin_id(detalle: str) -> str | None:
      # Patrón: ID de DEBIN (varía según banco)
      patron = r"DEBIN[:\s]*(\d+)"
      match = re.search(patron, detalle)
      return match.group(1) if match else None
  ```

- [ ] **Actualizar modelo Movimiento**
  ```python
  persona_nombre = Column(String, nullable=True)
  documento = Column(String, nullable=True, index=True)
  es_debin = Column(Boolean, default=False, index=True)
  debin_id = Column(String, nullable=True)
  ```

- [ ] **Integrar en consolidar.py**
  ```python
  from backend.core.extractores import (
      extraer_nombre, extraer_documento, es_debin, extraer_debin_id
  )

  # Al insertar movimiento:
  movimiento = Movimiento(
      fecha=fecha,
      descripcion=descripcion,
      monto=monto,
      categoria="SIN_CATEGORIA",
      persona_nombre=extraer_nombre(detalle),
      documento=extraer_documento(detalle),
      es_debin=es_debin(concepto, detalle),
      debin_id=extraer_debin_id(detalle) if es_debin(concepto, detalle) else None
  )
  ```

**Archivos afectados:**
- `backend/core/extractores.py` (nuevo)
- `backend/models/movimiento.py` (4 columnas nuevas)
- `backend/core/consolidar.py` (integración)
- Tests de extractores (nuevo)

**Tiempo estimado:** 3-4 días

---

#### 1.3 Edición Manual de Movimientos (UI) ⭐⭐⭐
**Objetivo:** Permitir corrección manual de categorizaciones desde el dashboard

**Estado CLI:**
```
El CLI tiene una interfaz interactiva que permite:
1. Ver movimientos sin clasificar
2. Seleccionar categoría correcta
3. Decidir si "recordar" la regla
4. Guardar cambios
```

**Tareas:**
- [ ] **Endpoints CRUD de movimientos**
  ```python
  # backend/api/routes.py

  @router.put("/movimientos/{id}")
  async def actualizar_movimiento(
      id: int,
      categoria: Optional[str] = None,
      subcategoria: Optional[str] = None,
      descripcion: Optional[str] = None,
      db: Session = Depends(get_db)
  ):
      mov = db.query(Movimiento).filter(Movimiento.id == id).first()
      if not mov:
          raise HTTPException(404, "Movimiento no encontrado")

      if categoria:
          mov.categoria = categoria
      if subcategoria:
          mov.subcategoria = subcategoria
      if descripcion:
          mov.descripcion = descripcion

      db.commit()
      return {"status": "success", "movimiento": mov}

  @router.delete("/movimientos/{id}")
  async def eliminar_movimiento(id: int, db: Session = Depends(get_db)):
      mov = db.query(Movimiento).filter(Movimiento.id == id).first()
      if not mov:
          raise HTTPException(404)

      db.delete(mov)
      db.commit()
      return {"status": "success"}
  ```

- [ ] **UI de edición en Dashboard**
  ```html
  <!-- frontend/templates/index.html -->

  <!-- Botones en cada fila de movimiento -->
  <div class="mov-row">
      <div class="mov-info">
          <span class="mov-fecha">${mov.fecha}</span>
          <span class="mov-desc">${mov.descripcion}</span>
          <span class="mov-categoria">${mov.categoria}</span>
      </div>
      <div class="mov-actions">
          <button onclick="editarMovimiento(${mov.id})">✏️</button>
          <button onclick="eliminarMovimiento(${mov.id})">🗑️</button>
      </div>
  </div>

  <!-- Modal de edición -->
  <div id="modal-editar" class="modal" style="display:none;">
      <div class="modal-content">
          <h3>Editar Movimiento</h3>
          <input id="edit-descripcion" type="text" />
          <select id="edit-categoria">
              <option value="INGRESOS">INGRESOS</option>
              <option value="EGRESOS">EGRESOS</option>
          </select>
          <select id="edit-subcategoria">
              <!-- Dinámico según categoría -->
          </select>
          <button onclick="guardarCambios()">Guardar</button>
          <button onclick="cerrarModal()">Cancelar</button>
      </div>
  </div>
  ```

- [ ] **JavaScript para edición**
  ```javascript
  // frontend/static/js/app.js

  let movimientoEditando = null;

  function editarMovimiento(id) {
      // Cargar datos del movimiento
      fetch(`/api/movimientos/${id}`)
          .then(r => r.json())
          .then(mov => {
              movimientoEditando = mov;
              document.getElementById('edit-descripcion').value = mov.descripcion;
              document.getElementById('edit-categoria').value = mov.categoria;
              cargarSubcategorias(mov.categoria);
              document.getElementById('modal-editar').style.display = 'block';
          });
  }

  async function guardarCambios() {
      const descripcion = document.getElementById('edit-descripcion').value;
      const categoria = document.getElementById('edit-categoria').value;
      const subcategoria = document.getElementById('edit-subcategoria').value;

      await fetch(`/api/movimientos/${movimientoEditando.id}`, {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({descripcion, categoria, subcategoria})
      });

      cerrarModal();
      await initDashboard();  // Refresh
  }
  ```

**Archivos afectados:**
- `backend/api/routes.py` (PUT y DELETE endpoints)
- `frontend/templates/index.html` (modal de edición)
- `frontend/static/js/app.js` (lógica de edición)
- `frontend/static/css/styles.css` (estilos del modal)

**Tiempo estimado:** 4-5 días

---

### 🟡 FASE 2: FUNCIONALIDADES IMPORTANTES (2 semanas)

#### 2.1 Sistema de Reglas Aprendibles ⭐⭐
**Objetivo:** Permitir que el sistema aprenda de correcciones manuales

**Estado CLI:**
- Archivo `data/reglas.json` con reglas dinámicas
- Al corregir manualmente, se puede "recordar" la regla
- Incrementa confianza con cada confirmación

**Tareas:**
- [ ] **Modelo de Reglas**
  ```python
  # backend/models/regla.py

  class ReglaCategorizacion(Base):
      __tablename__ = "reglas_categorizacion"

      id = Column(Integer, primary_key=True)
      patron = Column(String, nullable=False, unique=True)
      categoria = Column(String, nullable=False)
      subcategoria = Column(String, nullable=False)
      confianza = Column(Integer, default=50)  # 0-100
      veces_usada = Column(Integer, default=1)
      creada_por_usuario = Column(Boolean, default=True)
      created_at = Column(DateTime, default=datetime.utcnow)
  ```

- [ ] **Endpoint para crear regla**
  ```python
  @router.post("/reglas")
  async def crear_regla(
      patron: str,
      categoria: str,
      subcategoria: str,
      db: Session = Depends(get_db)
  ):
      # Verificar si ya existe
      existente = db.query(ReglaCategorizacion).filter(
          ReglaCategorizacion.patron == patron
      ).first()

      if existente:
          # Incrementar confianza
          existente.confianza = min(100, existente.confianza + 10)
          existente.veces_usada += 1
      else:
          # Crear nueva
          nueva = ReglaCategorizacion(
              patron=patron,
              categoria=categoria,
              subcategoria=subcategoria
          )
          db.add(nueva)

      db.commit()
      return {"status": "success"}
  ```

- [ ] **Integrar reglas en categorizador**
  ```python
  # backend/core/categorizar.py

  def categorizar_con_reglas_aprendidas(concepto: str, db: Session):
      # 1. Intentar con reglas aprendidas (mayor confianza)
      reglas = db.query(ReglaCategorizacion).order_by(
          ReglaCategorizacion.confianza.desc()
      ).all()

      for regla in reglas:
          if regla.patron.lower() in concepto.lower():
              return regla.categoria, regla.subcategoria, regla.confianza

      # 2. Fallback a reglas estáticas
      return categorizar_estatico(concepto)
  ```

- [ ] **UI: Checkbox "Recordar esta regla"**
  ```html
  <div class="modal-footer">
      <label>
          <input type="checkbox" id="recordar-regla" checked />
          Recordar esta regla para movimientos similares
      </label>
  </div>
  ```

**Archivos afectados:**
- `backend/models/regla.py` (nuevo)
- `backend/api/routes.py` (endpoint POST /reglas)
- `backend/core/categorizar.py` (integración)
- `frontend/templates/index.html` (checkbox)

**Tiempo estimado:** 4-5 días

---

#### 2.2 Detección Automática de Banco ⭐⭐
**Objetivo:** Identificar banco por estructura de columnas

**Estado CLI:**
```python
# El CLI detecta:
- Supervielle: si tiene exactamente 6 columnas base
- Galicia: si tiene 16 columnas con "Descripción", "Grupo de Conceptos"
```

**Tareas:**
- [ ] **Implementar detector de banco**
  ```python
  # backend/core/detectores.py

  def detectar_banco(df: pd.DataFrame) -> str:
      columnas = [c.lower().strip() for c in df.columns]

      # Supervielle: estructura limpia 6 columnas
      if len(columnas) == 6 and all(c in columnas for c in [
          'fecha', 'concepto', 'detalle', 'debito', 'credito', 'saldo'
      ]):
          return "Supervielle"

      # Galicia: 16 columnas con basura
      if len(columnas) == 16 and 'descripcion' in columnas and 'grupo de conceptos' in columnas:
          return "Galicia"

      return "Generico"

  def parsear_galicia(df: pd.DataFrame) -> pd.DataFrame:
      # Eliminar 10 columnas basura
      columnas_basura = [
          'origen', 'numero de terminal', 'observaciones cliente',
          'numero de comprobante', 'leyendas adicionales 1',
          'leyendas adicionales 2', 'leyendas adicionales 3',
          'leyendas adicionales 4', 'tipo de movimiento'
      ]
      df = df.drop(columns=[c for c in columnas_basura if c in df.columns])

      # Mapear columnas
      df = df.rename(columns={
          'descripcion': 'concepto',
          'debitos': 'debito',
          'creditos': 'credito'
      })

      # Combinar "Grupo de Conceptos" + "Concepto" → Detalle
      df['detalle'] = df['grupo de conceptos'].fillna('') + ' ' + df['concepto'].fillna('')

      return df
  ```

- [ ] **Integrar en consolidar.py**
  ```python
  from backend.core.detectores import detectar_banco, parsear_galicia

  def consolidar_excel(file_bytes, filename, db):
      df = pd.read_excel(file_bytes)

      # Detectar banco
      banco = detectar_banco(df)

      # Parsear según banco
      if banco == "Galicia":
          df = parsear_galicia(df)

      # Normalizar columnas (genérico)
      df = normalizar_columnas(df)

      # Insertar en DB con metadata de banco
      for _, row in df.iterrows():
          mov = Movimiento(
              ...,
              banco=banco  # Nueva columna
          )
  ```

- [ ] **Actualizar modelo Movimiento**
  ```python
  banco = Column(String, nullable=True)  # "Supervielle", "Galicia", "Generico"
  ```

**Archivos afectados:**
- `backend/core/detectores.py` (nuevo)
- `backend/core/consolidar.py` (integración)
- `backend/models/movimiento.py` (columna banco)

**Tiempo estimado:** 3-4 días

---

#### 2.3 Gráficos Interactivos (Chart.js) ⭐⭐
**Objetivo:** Visualizaciones como en el CLI

**Estado CLI:**
```
Dashboard HTML con:
- Pie chart: Ingresos por subcategoría
- Pie chart: Egresos por subcategoría
- Line chart: Flujo de caja diario
```

**Tareas:**
- [ ] **Endpoint de analytics**
  ```python
  # backend/api/routes.py

  @router.get("/analytics/pie-ingresos")
  async def pie_ingresos(mes: Optional[str] = None, db: Session = Depends(get_db)):
      query = db.query(
          Movimiento.subcategoria,
          func.sum(Movimiento.monto).label('total')
      ).filter(
          Movimiento.categoria == "INGRESOS",
          Movimiento.monto > 0
      )

      if mes:
          query = query.filter(func.strftime('%Y-%m', Movimiento.fecha) == mes)

      resultados = query.group_by(Movimiento.subcategoria).all()

      return {
          "labels": [r[0] for r in resultados],
          "data": [float(r[1]) for r in resultados]
      }

  @router.get("/analytics/pie-egresos")
  async def pie_egresos(mes: Optional[str] = None, db: Session = Depends(get_db)):
      # Similar a pie_ingresos
      ...

  @router.get("/analytics/flujo-diario")
  async def flujo_diario(mes: str, db: Session = Depends(get_db)):
      ingresos = db.query(
          func.date(Movimiento.fecha).label('dia'),
          func.sum(Movimiento.monto).label('total')
      ).filter(
          Movimiento.categoria == "INGRESOS",
          func.strftime('%Y-%m', Movimiento.fecha) == mes
      ).group_by(func.date(Movimiento.fecha)).all()

      egresos = db.query(
          func.date(Movimiento.fecha).label('dia'),
          func.sum(Movimiento.monto).label('total')
      ).filter(
          Movimiento.categoria == "EGRESOS",
          func.strftime('%Y-%m', Movimiento.fecha) == mes
      ).group_by(func.date(Movimiento.fecha)).all()

      return {
          "dias": [str(i[0]) for i in ingresos],
          "ingresos": [float(i[1]) for i in ingresos],
          "egresos": [abs(float(e[1])) for e in egresos]
      }
  ```

- [ ] **Página de Analytics**
  ```html
  <!-- frontend/templates/analytics.html -->

  <div class="charts-container">
      <div class="chart-card">
          <h3>Ingresos por Categoría</h3>
          <canvas id="pie-ingresos"></canvas>
      </div>

      <div class="chart-card">
          <h3>Egresos por Categoría</h3>
          <canvas id="pie-egresos"></canvas>
      </div>

      <div class="chart-card full-width">
          <h3>Flujo de Caja Diario</h3>
          <canvas id="line-flujo"></canvas>
      </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="/static/js/charts.js"></script>
  ```

- [ ] **JavaScript de gráficos**
  ```javascript
  // frontend/static/js/charts.js

  async function renderPieIngresos() {
      const res = await fetch('/api/analytics/pie-ingresos');
      const data = await res.json();

      new Chart(document.getElementById('pie-ingresos'), {
          type: 'pie',
          data: {
              labels: data.labels,
              datasets: [{
                  data: data.data,
                  backgroundColor: [
                      '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6'
                  ]
              }]
          }
      });
  }

  async function renderLineFluj() {
      const mes = document.getElementById('selector-mes').value;
      const res = await fetch(`/api/analytics/flujo-diario?mes=${mes}`);
      const data = await res.json();

      new Chart(document.getElementById('line-flujo'), {
          type: 'line',
          data: {
              labels: data.dias,
              datasets: [
                  {
                      label: 'Ingresos',
                      data: data.ingresos,
                      borderColor: '#10b981',
                      fill: false
                  },
                  {
                      label: 'Egresos',
                      data: data.egresos,
                      borderColor: '#ef4444',
                      fill: false
                  }
              ]
          }
      });
  }
  ```

**Archivos afectados:**
- `backend/api/routes.py` (3 endpoints analytics)
- `frontend/templates/analytics.html` (nuevo)
- `frontend/static/js/charts.js` (nuevo)
- `backend/api/main.py` (ruta /analytics)

**Tiempo estimado:** 3-4 días

---

#### 2.4 Exportación a Excel Ejecutivo ⭐⭐
**Objetivo:** Reporte Excel de 5 hojas como el CLI

**Estado CLI:**
```
Reporte Excel con 5 hojas:
1. Resumen: Métricas principales + desgloses
2. Ingresos: Todos los ingresos detallados
3. Egresos: Todos los egresos detallados
4. Prestadores: Top prestadores con totales
5. Sin Clasificar: Movimientos pendientes
```

**Tareas:**
- [ ] **Endpoint de exportación**
  ```python
  # backend/api/routes.py

  from io import BytesIO
  from fastapi.responses import StreamingResponse
  import openpyxl
  from openpyxl.styles import Font, Alignment, PatternFill

  @router.get("/reportes/excel")
  async def exportar_reporte_excel(
      mes: str,
      db: Session = Depends(get_db)
  ):
      # Crear workbook
      wb = openpyxl.Workbook()

      # Hoja 1: Resumen
      ws_resumen = wb.active
      ws_resumen.title = "Resumen"
      generar_hoja_resumen(ws_resumen, mes, db)

      # Hoja 2: Ingresos
      ws_ingresos = wb.create_sheet("Ingresos")
      generar_hoja_ingresos(ws_ingresos, mes, db)

      # Hoja 3: Egresos
      ws_egresos = wb.create_sheet("Egresos")
      generar_hoja_egresos(ws_egresos, mes, db)

      # Hoja 4: Prestadores
      ws_prestadores = wb.create_sheet("Prestadores")
      generar_hoja_prestadores(ws_prestadores, mes, db)

      # Hoja 5: Sin Clasificar
      ws_sin_clasificar = wb.create_sheet("Sin Clasificar")
      generar_hoja_sin_clasificar(ws_sin_clasificar, mes, db)

      # Guardar en buffer
      buffer = BytesIO()
      wb.save(buffer)
      buffer.seek(0)

      return StreamingResponse(
          buffer,
          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          headers={"Content-Disposition": f"attachment; filename=reporte_ejecutivo_{mes}.xlsx"}
      )

  def generar_hoja_resumen(ws, mes, db):
      # Header
      ws['A1'] = 'REPORTE EJECUTIVO MENSUAL'
      ws['A1'].font = Font(size=16, bold=True)

      # KPIs
      ws['A3'] = 'Total Ingresos'
      ws['B3'] = calcular_total_ingresos(mes, db)

      ws['A4'] = 'Total Egresos'
      ws['B4'] = calcular_total_egresos(mes, db)

      ws['A5'] = 'Balance'
      ws['B5'] = '=B3-B4'

      # ... más contenido ...
  ```

- [ ] **Botón en UI**
  ```html
  <button onclick="descargarExcel()">
      📊 Descargar Reporte Excel
  </button>

  <script>
  async function descargarExcel() {
      const mes = document.getElementById('mes-selector').value;
      window.location.href = `/api/reportes/excel?mes=${mes}`;
  }
  </script>
  ```

**Dependencias nuevas:**
```txt
openpyxl>=3.1.0  # Ya instalado
```

**Archivos afectados:**
- `backend/api/routes.py` (endpoint + helpers)
- `frontend/templates/reportes.html` (botón)

**Tiempo estimado:** 4-5 días

---

### 🟢 FASE 3: MEJORAS OPCIONALES (1-2 semanas)

#### 3.1 Top Prestadores
**Tareas:**
- [ ] Endpoint GET /api/prestadores/top?mes=YYYY-MM
- [ ] Vista en Dashboard o página separada
- [ ] Tabla ordenada por monto total

**Tiempo:** 1-2 días

---

#### 3.2 Selección de Archivos Específicos
**Tareas:**
- [ ] UI con checkboxes para seleccionar archivos
- [ ] Endpoint acepta lista de archivos
- [ ] Consolidación parcial

**Tiempo:** 2-3 días

---

## 📅 TIMELINE ESTIMADO

### **MES 1: Funcionalidades Críticas**
- Semana 1-2: Categorizador Cascada v2.0 (1.1)
- Semana 2: Extracción de Metadata (1.2)
- Semana 3-4: Edición Manual UI (1.3)

### **MES 2: Funcionalidades Importantes**
- Semana 1: Sistema de Reglas Aprendibles (2.1)
- Semana 1-2: Detección de Banco (2.2)
- Semana 3: Gráficos Chart.js (2.3)
- Semana 4: Exportación Excel (2.4)

### **MES 3: Opcional - Mejoras**
- Semana 1: Top Prestadores (3.1)
- Semana 2: Selección de archivos (3.2)
- Semana 3-4: Testing completo + refinamiento

---

## 🎯 HITOS CLAVE

| Hito | Fecha Estimada | Descripción |
|------|----------------|-------------|
| **v2.1.0** | +2 semanas | Categorizador Cascada + Metadata |
| **v2.2.0** | +1 mes | Edición manual funcionando |
| **v2.3.0** | +6 semanas | Gráficos + Excel + Reglas aprendibles |
| **v3.0.0** | +2 meses | PARIDAD COMPLETA CON CLI |

---

## 📊 MATRIZ DE PRIORIZACIÓN

### Quick Wins (Bajo esfuerzo, Alto impacto):
- ✅ Exportación Excel ejecutivo (2.4) - 4 días

### Críticos (Alto esfuerzo, Alto impacto):
- 🔴 Categorizador Cascada (1.1) - 7 días
- 🔴 Edición manual (1.3) - 5 días
- 🔴 Extracción metadata (1.2) - 4 días

### Importantes (Medio esfuerzo, Medio impacto):
- 🟡 Gráficos Chart.js (2.3) - 4 días
- 🟡 Detección banco (2.2) - 4 días
- 🟡 Sistema de reglas (2.1) - 5 días

### Opcionales (Bajo esfuerzo, Bajo impacto):
- 🟢 Top Prestadores (3.1) - 2 días
- 🟢 Selección archivos (3.2) - 3 días

---

## 💡 RECOMENDACIÓN DE INICIO

### **Empezar por (próximos 14 días):**

1. ✅ **Categorizador Cascada v2.0** (7 días)
   - Mayor impacto en calidad de datos
   - Base para todo lo demás

2. ✅ **Extracción de Metadata** (4 días)
   - Complementa el categorizador
   - Datos críticos para reportes

3. ✅ **Edición Manual UI** (5 días)
   - Permite corregir errores
   - Mejora UX inmediatamente

**Total**: ~16 días para tener la base sólida

Luego continuar con Fase 2 (gráficos, Excel, reglas).

---

## 🔍 COMPARATIVA FINAL: CLI vs WEB al completar plan

| Aspecto | CLI v2.0 | WEB v3.0 (post-plan) |
|---------|----------|---------------------|
| **Categorización** | ✅ 2 niveles, 37 reglas | ✅ Mismo sistema |
| **Metadata** | ✅ Nombres, CUIT, DEBIN | ✅ Mismo sistema |
| **Corrección manual** | ✅ CLI interactivo | ✅ UI web moderna |
| **Reglas aprendibles** | ✅ JSON persistente | ✅ Base de datos |
| **Reportes Excel** | ✅ 5 hojas | ✅ Mismo formato |
| **Gráficos** | ✅ Chart.js en HTML | ✅ Integrado en web |
| **Multi-banco** | ✅ Detección automática | ✅ Mismo sistema |
| **Dashboard** | ❌ Solo HTML estático | ✅ **MEJOR** (tiempo real) |
| **API** | ❌ No tiene | ✅ **MEJOR** (REST API) |
| **Multi-usuario** | ❌ No soporta | ✅ **MEJOR** (futuro) |
| **Batches** | ❌ No tiene | ✅ **MEJOR** (control total) |

**Resultado:** WEB será SUPERIOR al CLI en todos los aspectos

---

## 📝 CHECKLIST DE PARIDAD

### Consolidación
- [x] Normalización flexible de columnas
- [ ] Detección automática de banco
- [ ] Parser específico para Galicia
- [x] Guardado de archivos con timestamp
- [x] Inserción en base de datos

### Categorización
- [x] Sistema de 2 niveles (Concepto → Detalle)
- [x] 37 reglas de nivel 1
- [x] 24 patrones de refinamiento
- [x] Subcategorías (9 totales)
- [x] Confianza porcentual (0-100)

### Metadata
- [x] Extracción de nombres
- [x] Extracción de CUIT/CUIL/DNI
- [x] Detección de DEBIN
- [x] ID de DEBIN
- [x] UI de visualización (metadata.html)

### Corrección Manual
- [x] UI de edición de movimientos
- [x] Cambio de categoría/subcategoría
- [x] Edición de descripción
- [x] Eliminación de movimientos
- [ ] Sistema de "recordar regla" (opcional - ETAPA 4)

### Reportes
- [x] KPIs básicos (ingresos, egresos, balance)
- [x] **Reporte Ejecutivo Completo** (Saldos + Clasificación + Desgloses completos)
- [x] **Saldos Bancarios Reales** (Fix de paridad 100% con Excel CLI)
- [x] Desglose completo de ingresos por categoría
- [x] Desglose completo de egresos por categoría
- [x] Comparación mes anterior
- [ ] Top 10 prestadores
- [ ] Exportación a Excel (5 hojas)
- [ ] Gráficos Chart.js
- [ ] Flujo de caja diario

### Sistema
- [x] Batches con rollback
- [x] Dashboard en tiempo real
- [x] API REST documentada
- [ ] Reglas en base de datos
- [ ] Tests completos (>90% coverage)

---

## 🚀 ESTADO ACTUAL vs OBJETIVO

### Estado Actual (WEB v2.0)
```
Funcionalidades: 40% del CLI
├── Consolidación básica: ✅
├── Categorización simple: ⚠️ (solo 6 categorías)
├── Reportes básicos: ✅
├── Dashboard web: ✅ (MEJOR que CLI)
├── Batches: ✅ (NO existe en CLI)
└── API: ✅ (NO existe en CLI)
```

### Objetivo (WEB v3.0)
```
Funcionalidades: 120% del CLI
├── Consolidación avanzada: ✅
├── Categorización cascada: ✅ (mismo que CLI)
├── Metadata completa: ✅
├── Edición manual: ✅ (MEJOR que CLI)
├── Reportes completos: ✅ (Excel + gráficos)
├── Reglas aprendibles: ✅ (persistente en DB)
├── Dashboard web: ✅ (MEJOR que CLI)
├── Batches: ✅ (NO existe en CLI)
└── API: ✅ (NO existe en CLI)
```

---

## 📞 SOPORTE Y REFERENCIAS

### Documentación CLI Original
- `../sanarte_financiero/README.md`
- `../sanarte_financiero/src/` (código fuente)

### Documentación WEB Actual
- `RELEVAMIENTO_PROYECTO.md`
- `ROADMAP.md`
- `CONTROL_BATCHES_IMPLEMENTADO.md`

### Tests de Referencia
- `../sanarte_financiero/tests/` (26 tests del CLI)
- `./tests/` (tests actuales web)

---

## ✅ CONCLUSIÓN

Para alcanzar **paridad funcional con el CLI**, se deben implementar **principalmente 3 funcionalidades críticas**:

1. **Categorizador Cascada v2.0** (2 niveles, 37 reglas)
2. **Extracción de Metadata** (nombres, CUIT, DEBIN)
3. **Edición Manual UI** (corrección interactiva)

El resto son mejoras importantes pero no bloquean la paridad básica.

**Esfuerzo total estimado:** 6-8 semanas para paridad completa

**Esfuerzo para paridad crítica:** 2-3 semanas (solo las 3 funcionalidades críticas)

---

---

## 📊 TRABAJO ADICIONAL COMPLETADO (POST-ETAPA 3)

### ✅ Reporte Ejecutivo Completo en UI (17 dic 2024)

**Problema:** El endpoint `/api/reportes` devolvía JSON completo pero la UI `/reportes` solo mostraba KPIs + Top 5 egresos

**Solución implementada:**
- ✅ **4 secciones nuevas agregadas a la UI:**
  1. **Saldos Bancarios** - Tabla con saldo inicial, ingresos, egresos, variación, saldo final
  2. **Clasificación** - Movimientos totales, clasificados, sin clasificar, % clasificados
  3. **Desglose Ingresos Completo** - TODAS las categorías de ingresos (no solo top 5)
  4. **Desglose Egresos Completo** - TODAS las categorías de egresos (no solo top 5)

**Archivos modificados:**
- `frontend/templates/reportes.html` - 4 tablas HTML nuevas + JavaScript de renderizado
- `backend/core/reportes.py` - Backend ya tenía los datos completos, solo se expuso en UI

**Resultado:**
- ✅ La UI web ahora muestra **100% de la información** del reporte ejecutivo
- ✅ Paridad visual con lo que mostraba el PDF del CLI original
- ✅ Mejor organización y presentación que el Excel CLI

**Documentación:** `REPORTE_EJECUTIVO_COMPLETO.md`

---

### ✅ Fix Crítico: Saldos Bancarios 100% Precisos (17 dic 2024)

**Problema detectado:**
1. Diferencia de $160,551.83 entre saldos WEB y Excel CLI
2. Diferencia adicional de $418,305.00 por ordenamiento incorrecto

**Causa raíz:**
1. **Problema 1:** Sistema calculaba saldos sumando movimientos históricos en lugar de usar el saldo real del Excel
2. **Problema 2:** Ordenamiento de movimientos del mismo día por `id` en lugar de por `saldo`

**Solución implementada:**

**Fix 1: Columna `saldo` en DB**
- ✅ Agregada columna `saldo` al modelo `Movimiento`
- ✅ Migración de BD ejecutada (`backend/database/migrate_add_saldo.py`)
- ✅ Consolidador ahora extrae y guarda el saldo real del Excel
- ✅ Reportes usan saldos reales en lugar de calcularlos

**Fix 2: Ordenamiento correcto**
- ✅ Cambio en `backend/core/reportes.py`:
  - Primer movimiento: `ORDER BY fecha ASC, saldo DESC` (saldo más alto = primero)
  - Último movimiento: `ORDER BY fecha DESC, saldo ASC` (saldo más bajo = último)

**Archivos modificados:**
- `backend/models/movimiento.py` - Columna `saldo`
- `backend/database/migrate_add_saldo.py` - Script de migración
- `backend/core/consolidar.py` - Extraer y guardar saldo del Excel
- `backend/core/reportes.py` - Usar saldos reales + ordenamiento correcto

**Resultado final:**
- ✅ **Diferencia: $0.00** entre WEB y Excel CLI
- ✅ Saldo Inicial: $1,336,671.62 (exacto)
- ✅ Saldo Final: $14,930,103.81 (exacto)
- ✅ Total de discrepancias corregidas: $578,856.83

**Scripts de validación:**
- `test_saldos_fix.py` - Verifica paridad con Excel automáticamente
- `debug_primer_mov.py` - Analiza ordenamiento de movimientos

**Documentación:** `FIX_SALDOS_BANCARIOS.md` (completo con 2 problemas y soluciones)

---

---

### ✅ BUGFIX: Sincronización de Selectores de Período (18 dic 2024)

**Problema detectado:**
Los selectores de período (navbar vs selectores internos en reportes/analytics) podían quedar desincronizados:
- Usuario cambia selector interno → navbar NO se actualiza
- Usuario cambia navbar → selector interno NO se actualiza
- Resultado: navbar muestra "Nov 2025" pero página muestra "Oct 2025"

**Solución implementada:**

**Arquitectura del sistema:**
```
Usuario cambia selector (navbar O interno)
    ↓
PeriodoGlobal.setPeriodo(nuevoValor)
    ↓
Dispara evento "periodoChanged" SIEMPRE
    ↓
    ├─> Navbar actualiza selector global
    └─> Páginas internas:
        ├─> Sincronizan selector interno
        └─> Recargan datos
```

**Cambios realizados:**

1. **Navbar - Listener para sincronizar selector global**
   - ✅ Agregado listener en `periodo-global.js:123-129`
   - Escucha evento `periodoChanged` y actualiza selector global
   - Guard para prevenir loops: `if (selector.value !== p)`

2. **Reportes - Patrón bidireccional**
   - ✅ Refactorizado `reportes.html:457-470`
   - Selector interno change → SOLO `setPeriodo()` (no cargarReporte directo)
   - Listener de `periodoChanged` → sincroniza selector + recarga datos
   - Evita doble carga de datos

3. **Analytics - Mismo patrón**
   - ✅ Refactorizado `charts.js:52-67`
   - Patrón idéntico a reportes
   - Sincronización bidireccional completa

**Archivos modificados:**
- `frontend/static/js/periodo-global.js` - Listener en navbar
- `frontend/templates/reportes.html` - Patrón de sincronización
- `frontend/static/js/charts.js` - Patrón de sincronización

**Pruebas:**
- ✅ Test automatizado: `test_sincronizacion_selectores.html` (5 tests)
- ✅ Prevención de loops infinitos con guards
- ✅ No hay doble carga de datos
- ✅ Sincronización instantánea bidireccional

**Resultado:**
- ✅ Cambio en selector interno → navbar refleja mismo mes al instante
- ✅ Cambio en navbar → selector interno refleja mismo mes al instante
- ✅ Nunca quedan distintos valores
- ✅ Experiencia de usuario consistente entre páginas

**Documentación:** `BUGFIX_SINCRONIZACION_SELECTORES.md`

---

**Versión del Plan:** 1.2 (actualizado con bugfix de sincronización)
**Última Actualización:** 18 de Diciembre 2024
**Próxima Revisión:** Cada 2 semanas
