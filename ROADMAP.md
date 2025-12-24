# 🗺️ ROADMAP - TORO Investment Manager Web
## Plan de Desarrollo y Prioridades

**Versión Actual**: v2.0.0 (MVP)
**Fecha**: 14 de Diciembre 2024

---

## ⚠️ NOTA IMPORTANTE - CAMBIO EN PRIORIDADES

**ACTUALIZACIÓN (17 Dic 2024)**:
Se priorizó **ETAPA 4 - REGLAS APRENDIBLES** por sobre Presupuestos debido a su mayor impacto inmediato en UX.

✅ **ETAPA 4 - REGLAS APRENDIBLES**: COMPLETADA (17 Dic 2024)
- Sistema de aprendizaje basado en reglas
- Usuario puede "enseñar" al sistema mediante ediciones manuales
- Checkbox "Recordar regla" en modal de edición
- Categorización automática de movimientos similares
- +25% de precisión después de 3 meses de uso
- Ver: `ETAPA4_REGLAS_APRENDIBLES.md` para detalles completos

La funcionalidad de **Presupuestos** (originalmente FASE 4) se mantendrá como tarea pendiente.

---

## 🎯 Objetivo General

Evolucionar TORO de un MVP funcional a una plataforma completa de gestión financiera personal con múltiples usuarios, visualizaciones avanzadas y automatizaciones inteligentes.

---

## 📊 Priorización de Tareas

### Matriz de Prioridad (Esfuerzo vs Impacto)

```
Alto Impacto │
             │  [2]          [1]
             │  Medium       Quick Wins
             │  Effort       (PRIORIDAD ALTA)
             │
             │  [4]          [3]
Bajo Impacto │  Low          Low Effort
             │  Priority     (RELLENO)
             │
             └────────────────────────────
               Alto          Bajo
               Esfuerzo      Esfuerzo
```

---

## 🚀 FASE 1: Mejoras Críticas de UX (2-3 semanas)
**Objetivo**: Mejorar experiencia de usuario y estabilidad

### 1.1 Validación y Prevención de Errores ⚡ [Quick Win]
**Prioridad**: 🔴 ALTA
**Esfuerzo**: Bajo (2-3 días)
**Impacto**: Alto

#### Tareas:
- [ ] **Validación de duplicados en consolidación**
  ```python
  # backend/core/consolidar.py
  def es_duplicado(fecha, descripcion, monto, db):
      hash_mov = hashlib.md5(f"{fecha}{descripcion}{monto}".encode()).hexdigest()
      existe = db.query(Movimiento).filter(Movimiento.hash == hash_mov).first()
      return existe is not None

  # Agregar columna 'hash' a modelo Movimiento
  hash = Column(String, unique=True, index=True)
  ```

- [ ] **Preview de Excel antes de procesar**
  ```javascript
  // frontend/static/js/app.js
  async function previewExcel(file) {
      const formData = new FormData();
      formData.append('archivo', file);
      const res = await fetch('/api/preview-excel', {method: 'POST', body: formData});
      const data = await res.json();
      // Mostrar modal con: columnas detectadas, primeras 5 filas, total filas
  }
  ```

- [ ] **Validación de formato de Excel**
  - Verificar que tenga al menos 1 fila de datos
  - Verificar que los montos sean numéricos
  - Verificar que las fechas sean válidas

- [ ] **Mensajes de error más descriptivos**
  - En vez de "Error 400", mostrar exactamente qué columna falta
  - Sugerencias de corrección

**Resultado esperado**:
- ✅ 0 duplicados en DB
- ✅ Usuario sabe exactamente qué está mal antes de procesar
- ✅ 80% menos errores en upload

---

### 1.2 Feedback Visual y Loading States ⚡ [Quick Win]
**Prioridad**: 🔴 ALTA
**Esfuerzo**: Bajo (1-2 días)
**Impacto**: Alto

#### Tareas:
- [ ] **Spinners durante carga**
  ```html
  <!-- frontend/templates/index.html -->
  <div id="loading-spinner" class="spinner" style="display:none;">
      <div class="spinner-circle"></div>
      <p>Procesando Excel...</p>
  </div>
  ```

- [ ] **Toast notifications en vez de alerts**
  ```javascript
  // frontend/static/js/toast.js
  function showToast(message, type = 'success') {
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.textContent = message;
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
  }
  ```

- [ ] **Progress bar durante procesamiento**
  - Mostrar: "Consolidando... 1/3"
  - Luego: "Categorizando... 2/3"
  - Finalmente: "Generando reporte... 3/3"

- [ ] **Confirmación antes de acciones destructivas**
  ```javascript
  // Antes de eliminar movimientos
  if (!confirm('¿Estás seguro? Esta acción no se puede deshacer.')) {
      return;
  }
  ```

**Resultado esperado**:
- ✅ Usuario siempre sabe qué está pasando
- ✅ No hay "pantallas blancas" de espera
- ✅ Feedback inmediato de éxito/error

---

### 1.3 Edición Manual de Movimientos ⚡ [Quick Win]
**Prioridad**: 🔴 ALTA
**Esfuerzo**: Bajo-Medio (3-4 días)
**Impacto**: Alto

#### Tareas:
- [ ] **Endpoint PUT /api/movimientos/{id}**
  ```python
  # backend/api/routes.py
  @router.put("/movimientos/{id}")
  async def actualizar_movimiento(
      id: int,
      categoria: Optional[str] = None,
      descripcion: Optional[str] = None,
      db: Session = Depends(get_db)
  ):
      mov = db.query(Movimiento).filter(Movimiento.id == id).first()
      if not mov:
          raise HTTPException(404, "Movimiento no encontrado")

      if categoria:
          mov.categoria = categoria
      if descripcion:
          mov.descripcion = descripcion

      db.commit()
      return {"status": "success", "movimiento": mov}
  ```

- [ ] **Endpoint DELETE /api/movimientos/{id}**

- [ ] **Modal de edición en Dashboard**
  ```html
  <div id="edit-modal" class="modal">
      <h3>Editar Movimiento</h3>
      <input id="edit-descripcion" type="text" />
      <select id="edit-categoria">
          <option>ALIMENTACION</option>
          <option>COMBUSTIBLE</option>
          <!-- ... -->
      </select>
      <button onclick="guardarCambios()">Guardar</button>
  </div>
  ```

- [ ] **Botones de acción en cada movimiento**
  - Ícono lápiz → editar
  - Ícono basura → eliminar

**Resultado esperado**:
- ✅ Usuario puede corregir categorizaciones erróneas
- ✅ Usuario puede editar descripciones
- ✅ Usuario puede eliminar duplicados manualmente

---

### 1.4 Búsqueda y Filtros ⚡ [Quick Win]
**Prioridad**: 🟡 MEDIA-ALTA
**Esfuerzo**: Medio (4-5 días)
**Impacto**: Alto

#### Tareas:
- [ ] **Endpoint GET /api/movimientos con filtros**
  ```python
  @router.get("/movimientos")
  async def listar_movimientos(
      categoria: Optional[str] = None,
      fecha_desde: Optional[date] = None,
      fecha_hasta: Optional[date] = None,
      buscar: Optional[str] = None,
      limite: int = 50,
      offset: int = 0,
      db: Session = Depends(get_db)
  ):
      query = db.query(Movimiento)

      if categoria:
          query = query.filter(Movimiento.categoria == categoria)
      if fecha_desde:
          query = query.filter(Movimiento.fecha >= fecha_desde)
      if fecha_hasta:
          query = query.filter(Movimiento.fecha <= fecha_hasta)
      if buscar:
          query = query.filter(Movimiento.descripcion.contains(buscar))

      total = query.count()
      movimientos = query.offset(offset).limit(limite).all()

      return {
          "total": total,
          "movimientos": movimientos,
          "pagina": offset // limite + 1,
          "total_paginas": (total + limite - 1) // limite
      }
  ```

- [ ] **Barra de búsqueda en Dashboard**
  ```html
  <input
      type="search"
      id="search-input"
      placeholder="Buscar en descripción..."
      oninput="debounceSearch()"
  />
  ```

- [ ] **Filtros por categoría, fecha, rango de monto**

- [ ] **Paginación con botones Anterior/Siguiente**

**Resultado esperado**:
- ✅ Usuario puede encontrar cualquier movimiento rápidamente
- ✅ Filtros combinables
- ✅ Performance optimizada con paginación

---

## 🔐 FASE 2: Autenticación y Multi-Usuario (2-3 semanas)
**Objetivo**: Permitir múltiples usuarios con datos aislados

### 2.1 Sistema de Autenticación
**Prioridad**: 🔴 ALTA
**Esfuerzo**: Alto (1 semana)
**Impacto**: Muy Alto

#### Tareas:
- [ ] **Modelo User**
  ```python
  # backend/models/user.py
  class User(Base):
      __tablename__ = "users"

      id = Column(Integer, primary_key=True)
      email = Column(String, unique=True, nullable=False, index=True)
      username = Column(String, unique=True, nullable=False)
      hashed_password = Column(String, nullable=False)
      created_at = Column(DateTime, default=datetime.utcnow)
      is_active = Column(Boolean, default=True)

      # Relación con movimientos
      movimientos = relationship("Movimiento", back_populates="user")
  ```

- [ ] **Actualizar modelo Movimiento**
  ```python
  # backend/models/movimiento.py
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
  user = relationship("User", back_populates="movimientos")
  ```

- [ ] **Sistema JWT**
  ```python
  # backend/auth/jwt.py
  from jose import JWTError, jwt
  from passlib.context import CryptContext

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  SECRET_KEY = "tu-secret-key-super-segura"
  ALGORITHM = "HS256"

  def create_access_token(data: dict):
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(days=7)
      to_encode.update({"exp": expire})
      return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

  def get_current_user(token: str = Depends(oauth2_scheme)):
      # Decodifica JWT y retorna user
      pass
  ```

- [ ] **Endpoints de autenticación**
  - POST /api/auth/register
  - POST /api/auth/login
  - POST /api/auth/logout
  - GET /api/auth/me

- [ ] **Páginas de login/registro**
  ```html
  <!-- frontend/templates/login.html -->
  <form id="login-form">
      <input type="email" name="email" required />
      <input type="password" name="password" required />
      <button type="submit">Iniciar Sesión</button>
  </form>
  ```

- [ ] **Middleware de autenticación**
  ```python
  # Aplicar a todos los endpoints API
  current_user: User = Depends(get_current_user)

  # Filtrar movimientos por usuario
  movimientos = db.query(Movimiento).filter(
      Movimiento.user_id == current_user.id
  ).all()
  ```

**Dependencias nuevas**:
```txt
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
```

**Resultado esperado**:
- ✅ Múltiples usuarios pueden usar la app
- ✅ Cada usuario ve solo sus datos
- ✅ Login seguro con JWT
- ✅ Sesiones persistentes

---

## 📊 FASE 3: Visualizaciones y Analytics (2 semanas)
**Objetivo**: Gráficos y análisis visual de datos

### 3.1 Integración de Chart.js
**Prioridad**: 🟡 MEDIA
**Esfuerzo**: Medio (1 semana)
**Impacto**: Alto

#### Tareas:
- [ ] **Instalar Chart.js**
  ```html
  <!-- frontend/templates/base.html -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  ```

- [ ] **Pie Chart - Gastos por Categoría**
  ```javascript
  // frontend/static/js/charts.js
  async function renderPieChart() {
      const res = await fetch('/api/analytics/gastos-por-categoria');
      const data = await res.json();

      new Chart(document.getElementById('pie-chart'), {
          type: 'pie',
          data: {
              labels: data.categorias,
              datasets: [{
                  data: data.montos,
                  backgroundColor: [
                      '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981', '#06b6d4'
                  ]
              }]
          }
      });
  }
  ```

- [ ] **Line Chart - Evolución Mensual**
  ```javascript
  // Ingresos vs Egresos por mes (últimos 12 meses)
  ```

- [ ] **Bar Chart - Comparación Meses**
  ```javascript
  // Top 5 categorías comparando 3 meses
  ```

- [ ] **Endpoint /api/analytics/gastos-por-categoria**
  ```python
  @router.get("/analytics/gastos-por-categoria")
  async def gastos_por_categoria(
      mes: Optional[str] = None,
      current_user: User = Depends(get_current_user),
      db: Session = Depends(get_db)
  ):
      # Query agrupado por categoría
      resultados = db.query(
          Movimiento.categoria,
          func.sum(Movimiento.monto).label('total')
      ).filter(
          Movimiento.user_id == current_user.id,
          Movimiento.monto < 0
      ).group_by(Movimiento.categoria).all()

      return {
          "categorias": [r[0] for r in resultados],
          "montos": [abs(r[1]) for r in resultados]
      }
  ```

- [ ] **Página nueva: /analytics**

**Resultado esperado**:
- ✅ Visualización clara de gastos
- ✅ Identificación rápida de categorías problemáticas
- ✅ Tendencias mensuales visibles

---

### 3.2 Dashboard Mejorado con KPIs Visuales
**Prioridad**: 🟡 MEDIA
**Esfuerzo**: Bajo-Medio (3-4 días)
**Impaco**: Medio

#### Tareas:
- [ ] **Progress bars de presupuesto**
  ```html
  <div class="budget-progress">
      <div class="budget-header">
          <span>ALIMENTACION</span>
          <span>$45,000 / $60,000</span>
      </div>
      <div class="progress-bar">
          <div class="progress-fill" style="width: 75%; background: #f97316;"></div>
      </div>
  </div>
  ```

- [ ] **Sparklines (mini gráficos) en tiles**
  ```javascript
  // Mostrar tendencia de últimos 7 días en cada KPI
  ```

- [ ] **Indicadores de variación**
  ```html
  <div class="kpi-card">
      <h3>Gastos del Mes</h3>
      <div class="kpi-value">$123,456</div>
      <div class="kpi-delta negative">
          ↑ 15% vs mes anterior
      </div>
  </div>
  ```

**Resultado esperado**:
- ✅ Dashboard más informativo y accionable
- ✅ Usuario identifica tendencias al instante

---

## 💰 FASE 4: Presupuestos y Alertas (1-2 semanas)
**Objetivo**: Control proactivo de gastos

### 4.1 Sistema de Presupuestos
**Prioridad**: 🟡 MEDIA-ALTA
**Esfuerzo**: Medio (1 semana)
**Impacto**: Alto

#### Tareas:
- [ ] **Modelo Presupuesto**
  ```python
  # backend/models/presupuesto.py
  class Presupuesto(Base):
      __tablename__ = "presupuestos"

      id = Column(Integer, primary_key=True)
      user_id = Column(Integer, ForeignKey("users.id"))
      categoria = Column(String, nullable=False)
      monto_limite = Column(Float, nullable=False)
      mes = Column(String)  # "2024-12" o NULL para todos los meses
      notificar_en = Column(Float, default=0.8)  # Alertar al 80%
  ```

- [ ] **Endpoints de presupuestos**
  - POST /api/presupuestos
  - GET /api/presupuestos
  - PUT /api/presupuestos/{id}
  - DELETE /api/presupuestos/{id}

- [ ] **UI de gestión de presupuestos**
  ```html
  <div class="budget-manager">
      <h3>Mis Presupuestos</h3>
      <button onclick="addBudget()">+ Agregar Presupuesto</button>

      <div class="budget-list">
          <!-- Lista de presupuestos con edit/delete -->
      </div>
  </div>
  ```

- [ ] **Cálculo de gasto actual vs presupuesto**
  ```python
  def calcular_progreso_presupuesto(categoria, mes, user_id, db):
      presupuesto = db.query(Presupuesto).filter(...).first()
      gasto_actual = db.query(func.sum(Movimiento.monto)).filter(
          Movimiento.categoria == categoria,
          Movimiento.user_id == user_id,
          # filtro de mes
      ).scalar()

      return {
          "limite": presupuesto.monto_limite,
          "gastado": abs(gasto_actual),
          "porcentaje": (abs(gasto_actual) / presupuesto.monto_limite) * 100,
          "restante": presupuesto.monto_limite - abs(gasto_actual)
      }
  ```

**Resultado esperado**:
- ✅ Usuario define límites de gasto
- ✅ Visualiza progreso en tiempo real
- ✅ Recibe alertas cuando se acerca al límite

---

### 4.2 Sistema de Notificaciones
**Prioridad**: 🟡 MEDIA
**Esfuerzo**: Medio (4-5 días)
**Impacto**: Medio-Alto

#### Tareas:
- [ ] **Notificaciones in-app**
  ```html
  <div class="notification-bell" onclick="toggleNotifications()">
      🔔 <span class="badge">3</span>
  </div>

  <div id="notifications-dropdown">
      <div class="notification warning">
          ⚠️ Presupuesto ALIMENTACION al 85%
      </div>
      <div class="notification info">
          ℹ️ Nuevo movimiento categorizado
      </div>
  </div>
  ```

- [ ] **Modelo Notificación**
  ```python
  class Notificacion(Base):
      __tablename__ = "notificaciones"

      id = Column(Integer, primary_key=True)
      user_id = Column(Integer, ForeignKey("users.id"))
      tipo = Column(String)  # "presupuesto", "sistema", "recordatorio"
      mensaje = Column(String)
      leida = Column(Boolean, default=False)
      created_at = Column(DateTime, default=datetime.utcnow)
  ```

- [ ] **Tarea asíncrona para verificar presupuestos**
  ```python
  # backend/tasks/budget_checker.py
  # Cron job que cada noche verifica presupuestos
  # y crea notificaciones si están cerca del límite
  ```

- [ ] **Notificaciones por email (opcional)**
  - Usando SendGrid o similar
  - Resumen semanal por email

**Resultado esperado**:
- ✅ Usuario nunca se pasa del presupuesto sin darse cuenta
- ✅ Notificaciones centralizadas

---

## 🧠 FASE 5: Inteligencia y Automatización (2-3 semanas)
**Objetivo**: Categorización inteligente y predicciones

### 5.1 Mejora de Categorización con ML
**Prioridad**: 🟢 MEDIA-BAJA
**Esfuerzo**: Alto (1-2 semanas)
**Impacto**: Medio

#### Tareas:
- [ ] **Entrenamiento de modelo sklearn**
  ```python
  # backend/ml/categorizer.py
  from sklearn.feature_extraction.text import TfidfVectorizer
  from sklearn.naive_bayes import MultinomialNB
  from sklearn.pipeline import Pipeline

  def entrenar_modelo(db):
      # Obtener movimientos con categoría manual
      movimientos = db.query(Movimiento).filter(
          Movimiento.categoria != "SIN_CATEGORIA"
      ).all()

      X = [m.descripcion for m in movimientos]
      y = [m.categoria for m in movimientos]

      pipeline = Pipeline([
          ('tfidf', TfidfVectorizer()),
          ('clf', MultinomialNB())
      ])

      pipeline.fit(X, y)

      # Guardar modelo
      joblib.dump(pipeline, 'modelo_categorias.pkl')

  def predecir_categoria(descripcion):
      modelo = joblib.load('modelo_categorias.pkl')
      return modelo.predict([descripcion])[0]
  ```

- [ ] **Endpoint /api/ml/entrenar**
  - Permite re-entrenar el modelo con nuevos datos

- [ ] **Usar ML como fallback de reglas**
  ```python
  # Si no hay match en keywords, usar ML
  if categoria == "OTROS":
      categoria = predecir_categoria(descripcion)
  ```

- [ ] **Feedback loop**
  - Cuando usuario corrige una categoría, marcar para reentrenamiento

**Dependencias nuevas**:
```txt
scikit-learn>=1.3.0
joblib>=1.3.0
```

**Resultado esperado**:
- ✅ Categorización >90% de precisión
- ✅ Aprende de correcciones manuales
- ✅ Mejora continua con uso

---

### 5.2 Predicciones y Proyecciones
**Prioridad**: 🟢 BAJA
**Esfuerzo**: Medio-Alto (1 semana)
**Impacto**: Medio

#### Tareas:
- [ ] **Predicción de gasto fin de mes**
  ```python
  def predecir_gasto_fin_mes(categoria, user_id, db):
      # Calcular promedio diario del mes hasta hoy
      # Proyectar hasta fin de mes
      dias_transcurridos = datetime.now().day
      dias_totales = calendar.monthrange(year, month)[1]

      gasto_actual = calcular_gasto_mes_actual(categoria, user_id, db)
      promedio_diario = gasto_actual / dias_transcurridos
      proyeccion = promedio_diario * dias_totales

      return {
          "actual": gasto_actual,
          "proyectado": proyeccion,
          "dias_restantes": dias_totales - dias_transcurridos
      }
  ```

- [ ] **Mostrar en Dashboard**
  ```html
  <div class="projection-card">
      <h4>Proyección ALIMENTACION</h4>
      <div>Gastado: $45,000</div>
      <div>Proyectado fin de mes: $68,500</div>
      <div class="alert">⚠️ Excederá presupuesto en $8,500</div>
  </div>
  ```

**Resultado esperado**:
- ✅ Usuario anticipa problemas
- ✅ Puede ajustar comportamiento antes de fin de mes

---

## 🏦 FASE 6: Multi-Banco y Parsers (1-2 semanas)
**Objetivo**: Soportar múltiples formatos de extractos

### 6.1 Sistema de Parsers Configurables
**Prioridad**: 🟡 MEDIA
**Esfuerzo**: Alto (1-2 semanas)
**Impacto**: Muy Alto

#### Tareas:
- [ ] **Modelo ParserConfig**
  ```python
  # backend/models/parser_config.py
  class ParserConfig(Base):
      __tablename__ = "parser_configs"

      id = Column(Integer, primary_key=True)
      nombre = Column(String)  # "Supervielle", "Galicia", "BBVA"
      skip_rows = Column(Integer, default=0)
      columna_fecha = Column(String, default="Fecha")
      columna_concepto = Column(String, default="Concepto")
      columna_detalle = Column(String, default="Detalle")
      columna_debito = Column(String, default="Debito")
      columna_credito = Column(String, default="Credito")
      formato_fecha = Column(String, default="%d/%m/%Y")
      separador_decimal = Column(String, default=",")
  ```

- [ ] **Auto-detección de banco**
  ```python
  def detectar_banco(df):
      # Si tiene columna "Nro. Operación" → Supervielle
      # Si tiene columna "Ref." → Galicia
      # etc.
      if "Nro. Operación" in df.columns:
          return "Supervielle"
      elif "Ref." in df.columns:
          return "Galicia"
      else:
          return "Generico"
  ```

- [ ] **Parser dinámico**
  ```python
  def parsear_excel_dinamico(file_bytes, parser_config):
      df = pd.read_excel(file_bytes, skiprows=parser_config.skip_rows)

      # Mapear columnas según config
      df = df.rename(columns={
          parser_config.columna_fecha: "fecha",
          parser_config.columna_concepto: "concepto",
          # ...
      })

      # Parsear fechas según formato
      df['fecha'] = pd.to_datetime(df['fecha'], format=parser_config.formato_fecha)

      return df
  ```

- [ ] **UI para gestionar parsers**
  - Crear/editar configuraciones de bancos
  - Probar parser con Excel de muestra

**Resultado esperado**:
- ✅ Soporta extractos de cualquier banco
- ✅ Usuario configura su propio parser
- ✅ No necesita modificar código

---

## 🚀 FASE 7: Exportación y Reportes Avanzados (1 semana)
**Objetivo**: Exportar datos y reportes profesionales

### 7.1 Exportación a PDF
**Prioridad**: 🟡 MEDIA
**Esfuerzo**: Medio (3-4 días)
**Impacto**: Medio

#### Tareas:
- [ ] **Endpoint /api/reportes/pdf**
  ```python
  from reportlab.lib.pagesizes import A4
  from reportlab.pdfgen import canvas

  @router.get("/reportes/pdf")
  async def exportar_reporte_pdf(mes: str, current_user: User = Depends(get_current_user)):
      reporte = generar_reporte_ejecutivo(db, mes)

      # Crear PDF
      pdf_buffer = BytesIO()
      c = canvas.Canvas(pdf_buffer, pagesize=A4)

      # Header
      c.setFont("Helvetica-Bold", 16)
      c.drawString(100, 800, f"Reporte Ejecutivo - {reporte['periodo']}")

      # KPIs
      c.setFont("Helvetica", 12)
      c.drawString(100, 750, f"Ingresos: ${reporte['kpis']['ingresos_total']}")
      # ...

      c.save()
      pdf_buffer.seek(0)

      return StreamingResponse(
          pdf_buffer,
          media_type="application/pdf",
          headers={"Content-Disposition": f"attachment; filename=reporte_{mes}.pdf"}
      )
  ```

- [ ] **Botón "Descargar PDF" en página de reportes**

**Dependencias nuevas**:
```txt
reportlab>=4.0.0
```

---

### 7.2 Exportación a Excel
**Prioridad**: 🟢 BAJA
**Esfuerzo**: Bajo (1-2 días)
**Impacto**: Bajo

#### Tareas:
- [ ] **Endpoint /api/movimientos/excel**
  ```python
  @router.get("/movimientos/excel")
  async def exportar_movimientos_excel(
      fecha_desde: date,
      fecha_hasta: date,
      current_user: User = Depends(get_current_user)
  ):
      movimientos = db.query(Movimiento).filter(...).all()

      df = pd.DataFrame([
          {
              'Fecha': m.fecha,
              'Descripcion': m.descripcion,
              'Monto': m.monto,
              'Categoria': m.categoria
          }
          for m in movimientos
      ])

      excel_buffer = BytesIO()
      df.to_excel(excel_buffer, index=False)
      excel_buffer.seek(0)

      return StreamingResponse(
          excel_buffer,
          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          headers={"Content-Disposition": "attachment; filename=movimientos.xlsx"}
      )
  ```

---

## 🐳 FASE 8: DevOps y Deploy (1 semana)
**Objetivo**: Deployment profesional y CI/CD

### 8.1 Dockerización
**Prioridad**: 🟡 MEDIA
**Esfuerzo**: Medio (2-3 días)
**Impacto**: Alto

#### Tareas:
- [ ] **Dockerfile**
  ```dockerfile
  # Dockerfile
  FROM python:3.11-slim

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  EXPOSE 8000

  CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **Docker Compose**
  ```yaml
  # docker-compose.yml
  version: '3.8'

  services:
    app:
      build: .
      ports:
        - "8000:8000"
      environment:
        - DATABASE_URL=postgresql://postgres:password@db:5432/toro
      depends_on:
        - db
      volumes:
        - ./output:/app/output

    db:
      image: postgres:15
      environment:
        POSTGRES_DB: toro
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: password
      volumes:
        - postgres_data:/var/lib/postgresql/data

  volumes:
    postgres_data:
  ```

- [ ] **Migrar de SQLite a PostgreSQL**
  ```python
  # Para producción usar PostgreSQL en vez de SQLite
  DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://...")
  ```

**Resultado esperado**:
- ✅ Deploy con un comando: `docker-compose up`
- ✅ Entorno reproducible
- ✅ Base de datos persistente

---

### 8.2 CI/CD con GitHub Actions
**Prioridad**: 🟢 BAJA
**Esfuerzo**: Bajo-Medio (2-3 días)
**Impacto**: Medio

#### Tareas:
- [ ] **.github/workflows/test.yml**
  ```yaml
  name: Tests

  on: [push, pull_request]

  jobs:
    test:
      runs-on: ubuntu-latest

      steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/

      - name: Check coverage
        run: pytest --cov=backend tests/
  ```

- [ ] **Deploy automático a Railway/Render**

---

## 🧪 FASE 9: Testing (Continuo)
**Objetivo**: Cobertura de tests >80%

### 9.1 Tests Unitarios
**Prioridad**: 🔴 ALTA (iniciar ya)
**Esfuerzo**: Continuo
**Impacto**: Muy Alto

#### Tareas:
- [ ] **Tests de consolidar.py**
  ```python
  # tests/test_consolidar.py
  def test_normalizar_columna():
      assert _norm_col("  Débito  ") == "debito"
      assert _norm_col("CRÉDITO") == "credito"
      assert _norm_col("Fecha") == "fecha"

  def test_consolidar_excel_valido():
      # Mock de archivo Excel
      # Verificar que inserta movimientos correctamente
      pass

  def test_consolidar_excel_columnas_faltantes():
      # Verificar que lanza ValueError
      pass
  ```

- [ ] **Tests de categorizar.py**
- [ ] **Tests de reportes.py**
- [ ] **Tests de endpoints API**

**Dependencias nuevas**:
```txt
pytest>=7.4.0
pytest-cov>=4.1.0
httpx>=0.24.0  # Para test client de FastAPI
```

---

## 📅 Timeline Sugerido

### **MES 1: UX y Estabilidad**
- Semana 1-2: Fase 1 (Mejoras UX)
- Semana 3-4: Fase 2 (Autenticación)

### **MES 2: Analytics y Features**
- Semana 1-2: Fase 3 (Visualizaciones)
- Semana 3-4: Fase 4 (Presupuestos)

### **MES 3: Inteligencia y Deploy**
- Semana 1-2: Fase 5 (ML) + Fase 6 (Multi-Banco)
- Semana 3-4: Fase 7 (Reportes) + Fase 8 (DevOps)

### **CONTINUO: Testing**
- Fase 9 se ejecuta en paralelo desde el principio

---

## 🎯 Hitos Clave

| Hito | Fecha Estimada | Descripción |
|------|----------------|-------------|
| **v2.1.0** | +2 semanas | UX mejorada + Validaciones |
| **v2.2.0** | +1 mes | Multi-usuario con autenticación |
| **v2.3.0** | +6 semanas | Gráficos y analytics |
| **v2.4.0** | +2 meses | Presupuestos y alertas |
| **v3.0.0** | +3 meses | ML + Multi-banco + Deploy |

---

## 💡 Recomendación de Inicio

### **Empezar por (próximos 7 días):**

1. ✅ **Validación de duplicados** (1 día)
   - Mayor impacto inmediato en calidad de datos

2. ✅ **Loading spinners y toasts** (1 día)
   - Mejora percepción de velocidad

3. ✅ **Edición manual de movimientos** (3 días)
   - Función más pedida por usuarios

4. ✅ **Tests básicos** (2 días)
   - Prevenir regresiones futuras

**Total**: ~7 días para tener v2.1.0 lista

---

## 📊 Métricas de Éxito

### KPIs a medir:

- **Calidad de Datos**:
  - % de duplicados en DB (objetivo: 0%)
  - % de movimientos categorizados correctamente (objetivo: >90%)

- **Engagement**:
  - Usuarios activos semanalmente
  - Archivos procesados por usuario/mes
  - Tiempo promedio en la app

- **Performance**:
  - Tiempo de procesamiento de Excel (objetivo: <3s)
  - Tiempo de carga del dashboard (objetivo: <1s)
  - Uptime (objetivo: >99%)

- **Satisfacción**:
  - NPS (Net Promoter Score)
  - Errores reportados por usuario
  - Adopción de nuevas features

---

## ❓ Decisiones Pendientes

1. **Base de datos en producción**: ¿PostgreSQL o MySQL?
2. **Hosting**: ¿Railway, Render, AWS, DigitalOcean?
3. **Notificaciones**: ¿Solo in-app o también email/SMS?
4. **Modelo de negocio**: ¿Freemium, suscripción, one-time payment?
5. **Mobile**: ¿Hacer app nativa o PWA?

---

**Documento vivo** - Actualizar según prioridades y feedback de usuarios

**Próxima revisión**: 21 de Diciembre 2024
