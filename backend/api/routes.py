"""
Rutas API de TORO Investment Manager
Endpoints para procesamiento financiero
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date
from io import BytesIO
import pandas as pd
import re

from backend.database.connection import get_db
from backend.models.movimiento import Movimiento
from backend.models.import_batch import ImportBatch
from backend.core.consolidar import consolidar_excel
from backend.core.categorizar import categorizar_movimientos  # Legacy (backup)
from backend.core.categorizador_cascada import categorizar_movimientos as categorizar_cascada
from backend.core.reportes import generar_reporte_ejecutivo
from backend.core.batches import anular_batch
from backend.core.insights import generar_insights
from backend.core.categorias_catalogo import load_catalog, get_tree

router = APIRouter(prefix="/api", tags=["TORO API"])

# ============================================
# ENDPOINT 1: CONSOLIDAR EXTRACTOS
# ============================================
@router.post("/consolidar")
async def consolidar_extractos(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if not archivo.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(400, "Solo se aceptan archivos Excel (.xlsx o .xls)")

        contenido = await archivo.read()
        resultado = consolidar_excel(contenido, archivo.filename, db)

        return JSONResponse({
            "status": "success",
            "mensaje": f"Extracto consolidado: {resultado['insertados']} movimientos insertados",
            "archivo": archivo.filename,
            "insertados": resultado["insertados"],
            "columnas_detectadas": resultado["columnas_detectadas"],
            "archivo_guardado": resultado["archivo_guardado"],
            "batch_id": resultado["batch_id"]
        })

    except ValueError as e:
        error_msg = str(e)
        if error_msg.startswith("DUPLICATE_FILE:"):
            raise HTTPException(status_code=409, detail=error_msg.replace("DUPLICATE_FILE: ", ""))
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {e}")


# ============================================
# ENDPOINT 2: CATEGORIZAR MOVIMIENTOS (Motor Cascada v2.0)
# ============================================
@router.post("/categorizar")
async def categorizar(db: Session = Depends(get_db)):
    """
    Categoriza movimientos usando el motor en cascada de 2 niveles.

    Actualiza los campos:
    - categoria: INGRESOS, EGRESOS, OTROS
    - subcategoria: Transferencias, Prestadores_Farmacias, etc.
    - confianza_porcentaje: 0-100%
    """
    try:
        # Usar motor cascada v2.0
        r = categorizar_cascada(db, solo_sin_categoria=True) or {}

        return JSONResponse({
            "status": "success",
            "mensaje": f"Categorizacion completada: {r.get('categorizados', 0)} movimientos categorizados",
            "motor": r.get("motor", "CategorizadorCascada v2.0"),
            "procesados": r.get("procesados", 0),
            "categorizados": r.get("categorizados", 0),
            "sin_match": r.get("sin_match", 0),
            "refinados_nivel2": r.get("refinados_nivel2", 0),
            "porcentaje_categorizados": r.get("porcentaje_categorizados", 0),
            "porcentaje_refinados": r.get("porcentaje_refinados", 0),
            "categorias_distintas": r.get("categorias_distintas", []),
            "top_categorias": r.get("top_categorias", []),
            "top_subcategorias": r.get("top_subcategorias", [])
        })

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error categorizando movimientos: {e}")


# ============================================
# ENDPOINT 3: GENERAR REPORTES
# ============================================
@router.get("/reportes")
async def obtener_reportes(
    mes: Optional[str] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        mes = period or mes
        if mes:
            try:
                year, month = map(int, mes.split("-"))
                if month < 1 or month > 12:
                    raise ValueError
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de mes invalido. Use YYYY-MM (ej: 2024-12)"
                )

        reporte = generar_reporte_ejecutivo(db, mes)
        return JSONResponse({"status": "success", "reporte": reporte})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {e}")


# ============================================
# ENDPOINT: INSIGHTS FINANCIEROS/OPERATIVOS
# ============================================
@router.get("/insights")
async def obtener_insights(
    mes: Optional[str] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Genera insights financieros/operativos del período.
    Los insights describen PATRONES del negocio/operación, NO estado de proyecto.

    Args:
        mes: Mes en formato YYYY-MM (opcional)
        period: Alias de mes (formato YYYY-MM, opcional)

    Returns:
        Lista de insights con title, message, action
    """
    try:
        mes = period or mes
        if mes:
            try:
                year, month = map(int, mes.split("-"))
                if month < 1 or month > 12:
                    raise ValueError
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de mes inválido. Use YYYY-MM (ej: 2024-12)"
                )

        # Generar reporte ejecutivo (fuente de datos)
        reporte = generar_reporte_ejecutivo(db, mes)

        # Generar insights basados en el reporte
        insights_objects = generar_insights(reporte, db, mes)

        # Convertir a dict
        insights = [insight.to_dict() for insight in insights_objects]

        return JSONResponse({
            "status": "success",
            "insights": insights,
            "mes": mes or "todos"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando insights: {e}")


# ============================================
# ENDPOINT 4: PROCESO COMPLETO (FIX DEFINITIVO)
# ============================================
@router.post("/proceso-completo")
async def proceso_completo(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if not archivo.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(400, "Solo se aceptan archivos Excel")

        contenido = await archivo.read()

        # 1️⃣ CONSOLIDAR
        r_consolidar = consolidar_excel(contenido, archivo.filename, db)

        # 2️⃣ CATEGORIZAR (DEFENSIVO)
        r_cat = categorizar_movimientos(db, solo_sin_categoria=True) or {}

        # 3️⃣ REPORTE
        r_reporte = generar_reporte_ejecutivo(db, mes=None)

        return JSONResponse({
            "status": "success",
            "mensaje": f"Proceso completo exitoso: {r_consolidar.get('insertados', 0)} movimientos procesados",
            "archivo": archivo.filename,
            "batch_id": r_consolidar.get("batch_id"),
            "consolidar": {
                "insertados": r_consolidar.get("insertados", 0),
                "columnas_detectadas": r_consolidar.get("columnas_detectadas", []),
                "archivo_guardado": r_consolidar.get("archivo_guardado"),
                "batch_id": r_consolidar.get("batch_id")
            },
            "categorizar": {
                "procesados": r_cat.get("procesados", 0),
                "categorizados": r_cat.get("categorizados", 0),
                "sin_match": r_cat.get("sin_match", 0),
                "categorias_distintas": r_cat.get("categorias_distintas", [])
            },
            "reporte": r_reporte
        })

    except ValueError as e:
        error_msg = str(e)
        if error_msg.startswith("DUPLICATE_FILE:"):
            raise HTTPException(status_code=409, detail=error_msg.replace("DUPLICATE_FILE: ", ""))
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en proceso completo: {e}")


# ============================================
# ENDPOINT 5: DASHBOARD DATA
# ============================================
@router.get("/dashboard")
async def obtener_datos_dashboard(
    batch_id: Optional[int] = Query(None, description="ID del batch a mostrar. Si no se especifica, muestra el último batch"),
    mostrar_historico: bool = Query(False, description="Si es True, muestra todos los movimientos históricos"),
    db: Session = Depends(get_db)
):
    try:
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year

        # Determinar qué batch mostrar
        if mostrar_historico:
            # Mostrar todos los movimientos (sin filtro de batch, incluye legacy)
            batch_filter = None
            batch_info = "Mostrando histórico completo"
            incluir_legacy = True
        elif batch_id is not None:
            # Mostrar batch específico
            batch_filter = batch_id
            batch_obj = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
            if not batch_obj:
                raise HTTPException(status_code=404, detail=f"Batch {batch_id} no encontrado")
            batch_info = f"Mostrando batch #{batch_id} ({batch_obj.filename})"
            incluir_legacy = False
        else:
            # Por defecto: mostrar el último batch
            ultimo_batch = db.query(ImportBatch).order_by(ImportBatch.imported_at.desc()).first()
            if ultimo_batch:
                batch_filter = ultimo_batch.id
                batch_info = f"Mostrando último batch #{ultimo_batch.id} ({ultimo_batch.filename})"
                incluir_legacy = False
            else:
                # NO HAY BATCHES: No mostrar movimientos legacy
                # Retornar dashboard vacío
                return JSONResponse({
                    "resumen_cuenta": {
                        "saldo_total": 0.0,
                        "movimientos_mes": 0,
                        "categorias_activas": 0
                    },
                    "ultimos_movimientos": [],
                    "mensaje": "No hay batches importados",
                    "batch_id": None,
                    "mostrar_historico": False
                })

        # Construir query base
        query_base = db.query(Movimiento)
        if batch_filter is not None:
            query_base = query_base.filter(Movimiento.batch_id == batch_filter)
        elif not incluir_legacy:
            # Si no hay batch_filter y no incluir legacy, no mostrar nada
            query_base = query_base.filter(Movimiento.batch_id.isnot(None))

        # Saldo total
        saldo_query = db.query(func.sum(Movimiento.monto))
        if batch_filter is not None:
            saldo_query = saldo_query.filter(Movimiento.batch_id == batch_filter)
        elif not incluir_legacy:
            saldo_query = saldo_query.filter(Movimiento.batch_id.isnot(None))

        saldo_total = saldo_query.scalar() or 0.0

        # Movimientos del mes
        movimientos_mes = query_base.filter(
            extract("month", Movimiento.fecha) == mes_actual,
            extract("year", Movimiento.fecha) == anio_actual
        ).count()

        # Categorías activas
        cat_query = db.query(func.count(func.distinct(Movimiento.categoria)))
        if batch_filter is not None:
            cat_query = cat_query.filter(Movimiento.batch_id == batch_filter)
        elif not incluir_legacy:
            cat_query = cat_query.filter(Movimiento.batch_id.isnot(None))

        categorias_activas = cat_query.filter(
            Movimiento.categoria.isnot(None),
            Movimiento.categoria != "",
            Movimiento.categoria != "SIN_CATEGORIA"
        ).scalar() or 0

        # Últimos movimientos
        ultimos = query_base.order_by(Movimiento.fecha.desc()).limit(10).all()

        ultimos_movimientos = [
            {
                "id": m.id,
                "fecha": m.fecha.isoformat(),
                "descripcion": m.descripcion,
                "monto": m.monto,
                "categoria": m.categoria or "SIN_CATEGORIA",
                "subcategoria": m.subcategoria
            }
            for m in ultimos
        ]

        total_movimientos = query_base.count()
        mensaje = (
            "Sin datos aún"
            if total_movimientos == 0
            else f"{batch_info} - {total_movimientos} movimientos"
        )

        return JSONResponse({
            "resumen_cuenta": {
                "saldo_total": round(saldo_total, 2),
                "movimientos_mes": movimientos_mes,
                "categorias_activas": categorias_activas
            },
            "ultimos_movimientos": ultimos_movimientos,
            "mensaje": mensaje,
            "batch_id": batch_filter,
            "mostrar_historico": mostrar_historico
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINT 6: LISTAR BATCHES
# ============================================
@router.get("/batches")
async def listar_batches(db: Session = Depends(get_db)):
    """
    Lista todos los batches importados, ordenados por fecha de importación (más reciente primero).

    Returns:
        200: Lista de batches
    """
    try:
        batches = db.query(ImportBatch).order_by(ImportBatch.imported_at.desc()).all()

        resultado = [
            {
                "id": batch.id,
                "filename": batch.filename,
                "imported_at": batch.imported_at.isoformat(),
                "rows_inserted": batch.rows_inserted
            }
            for batch in batches
        ]

        return JSONResponse(resultado)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando batches: {str(e)}")


# ============================================
# ENDPOINT 7: ROLLBACK DE BATCH
# ============================================
@router.delete("/batches/{batch_id}")
async def eliminar_batch(batch_id: int, db: Session = Depends(get_db)):
    """
    Elimina un batch completo y todos sus movimientos asociados.

    Operación ATÓMICA: si falla alguna parte, se revierte todo (rollback).

    Args:
        batch_id: ID del batch a eliminar

    Returns:
        200: Batch eliminado exitosamente
        404: Batch no encontrado
        500: Error en la operación
    """
    try:
        # Delegar a la lógica core
        resultado = anular_batch(db, batch_id)
        return JSONResponse(resultado)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando batch: {str(e)}"
        )


# ============================================
# ENDPOINT 8: CONFIGURACION
# ============================================
@router.get("/configuracion")
async def obtener_configuracion():
    return JSONResponse({
        "bancos_soportados": ["Supervielle", "Galicia"],
        "version": "2.1.0",
        "modo": "produccion",
        "estado": "operativo"
    })
    
    
# ============================================
# ENDPOINT: LISTAR MOVIMIENTOS (para UI Metadata - ETAPA 2.4)
# ============================================
@router.get("/movimientos")
async def listar_movimientos(
    con_metadata: bool = False,
    con_debin: bool = False,
    con_documento: bool = False,
    con_nombre: bool = False,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    # Base: movimientos más nuevos primero
    query = db.query(Movimiento)

    # Filtros simples
    if con_debin:
        query = query.filter(Movimiento.es_debin == True)

    if con_documento:
        query = query.filter(Movimiento.documento.isnot(None)).filter(Movimiento.documento != "")

    if con_nombre:
        query = query.filter(Movimiento.persona_nombre.isnot(None)).filter(Movimiento.persona_nombre != "")

    if con_metadata:
        query = query.filter(
            (Movimiento.persona_nombre.isnot(None) & (Movimiento.persona_nombre != "")) |
            (Movimiento.documento.isnot(None) & (Movimiento.documento != "")) |
            (Movimiento.debin_id.isnot(None) & (Movimiento.debin_id != ""))
        )

    # Seguridad: límite para no matar el navegador
    limit = max(1, min(limit, 1000))

    movimientos = query.order_by(Movimiento.fecha.desc()).limit(limit).all()

    # Respuesta JSON lista para la tabla
    return [
        {
            "id": m.id,
            "fecha": m.fecha.isoformat(),
            "monto": m.monto,
            "descripcion": m.descripcion,
            "categoria": m.categoria,
            "subcategoria": m.subcategoria,
            "confianza_porcentaje": m.confianza_porcentaje,
            "persona_nombre": m.persona_nombre,
            "documento": m.documento,
            "es_debin": m.es_debin,
            "debin_id": m.debin_id,
            "batch_id": m.batch_id,
        }
        for m in movimientos
    ]


# ============================================
# ENDPOINT: EDITAR MOVIMIENTO (ETAPA 3)
# ============================================
@router.put("/movimientos/{movimiento_id}")
async def actualizar_movimiento(
    movimiento_id: int,
    descripcion: Optional[str] = None,
    categoria: Optional[str] = None,
    subcategoria: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Actualiza un movimiento existente.

    Args:
        movimiento_id: ID del movimiento a actualizar
        descripcion: Nueva descripción (opcional)
        categoria: Nueva categoría (opcional)
        subcategoria: Nueva subcategoría (opcional)

    Returns:
        200: Movimiento actualizado exitosamente
        404: Movimiento no encontrado
        500: Error en la operación
    """
    try:
        # Buscar movimiento
        movimiento = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()

        if not movimiento:
            raise HTTPException(status_code=404, detail=f"Movimiento {movimiento_id} no encontrado")

        # Actualizar campos si se proporcionaron
        campos_actualizados = []
        categorizado_manualmente = False

        if descripcion is not None:
            movimiento.descripcion = descripcion
            campos_actualizados.append("descripcion")

        if categoria is not None:
            movimiento.categoria = categoria
            campos_actualizados.append("categoria")
            categorizado_manualmente = True

        if subcategoria is not None:
            movimiento.subcategoria = subcategoria
            campos_actualizados.append("subcategoria")
            categorizado_manualmente = True

        # Si no se proporcionó ningún campo, retornar error
        if not campos_actualizados:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar al menos un campo para actualizar (descripcion, categoria o subcategoria)"
            )

        # FIX CRÍTICO: Si se actualizó categoría/subcategoría, setear confianza=100 y fuente=manual
        if categorizado_manualmente:
            movimiento.confianza_porcentaje = 100
            if hasattr(movimiento, 'confianza_fuente'):
                movimiento.confianza_fuente = "manual"

        # Guardar cambios
        db.commit()
        db.refresh(movimiento)

        return JSONResponse({
            "status": "success",
            "mensaje": f"Movimiento {movimiento_id} actualizado exitosamente",
            "campos_actualizados": campos_actualizados,
            "movimiento": {
                "id": movimiento.id,
                "fecha": movimiento.fecha.isoformat(),
                "monto": movimiento.monto,
                "descripcion": movimiento.descripcion,
                "categoria": movimiento.categoria,
                "subcategoria": movimiento.subcategoria
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando movimiento: {str(e)}"
        )


# ============================================
# ENDPOINT: ELIMINAR MOVIMIENTO (ETAPA 3)
# ============================================
@router.delete("/movimientos/{movimiento_id}")
async def eliminar_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un movimiento individual.

    IMPORTANTE: Esta operación es irreversible.

    Args:
        movimiento_id: ID del movimiento a eliminar

    Returns:
        200: Movimiento eliminado exitosamente
        404: Movimiento no encontrado
        500: Error en la operación
    """
    try:
        # Buscar movimiento
        movimiento = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()

        if not movimiento:
            raise HTTPException(status_code=404, detail=f"Movimiento {movimiento_id} no encontrado")

        # Guardar info para el response
        info_movimiento = {
            "id": movimiento.id,
            "fecha": movimiento.fecha.isoformat(),
            "descripcion": movimiento.descripcion,
            "monto": movimiento.monto,
            "batch_id": movimiento.batch_id
        }

        # Eliminar movimiento
        db.delete(movimiento)
        db.commit()

        return JSONResponse({
            "status": "success",
            "mensaje": f"Movimiento {movimiento_id} eliminado exitosamente",
            "movimiento_eliminado": info_movimiento
        })

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando movimiento: {str(e)}"
        )


# ============================================
# ENDPOINT 12: ANALYTICS - PIE CHART INGRESOS
# ============================================
@router.get("/analytics/pie-ingresos")
async def pie_ingresos(
    mes: Optional[str] = Query(None, description="Mes en formato YYYY-MM (opcional)"),
    period: Optional[str] = Query(None, description="Alias de mes (formato YYYY-MM, opcional)"),
    db: Session = Depends(get_db)
):
    """
    Retorna datos para pie chart de ingresos por categoría.
    Usa la misma fuente de verdad que /api/reportes (generar_reporte_ejecutivo).

    Parámetros:
    - mes: Filtro opcional por mes (YYYY-MM)
    - period: Alias de mes (formato YYYY-MM, opcional)

    Retorna:
    - status: "success"
    - data: Lista de objetos {label, value}
    - total: Total de ingresos (positivo)
    """
    try:
        mes = period or mes
        # Usar la misma fuente de verdad que /api/reportes
        reporte = generar_reporte_ejecutivo(db, mes)

        # Extraer desglose de ingresos del reporte
        desglose_ingresos = reporte.get("desglose_ingresos", [])

        # Formatear para charts.js
        data = [
            {
                "label": item["categoria"],
                "value": item["monto"]
            }
            for item in desglose_ingresos
        ]

        # Total de ingresos del reporte (siempre positivo)
        total = reporte["saldos"]["ingresos_total"]

        return JSONResponse({
            "status": "success",
            "data": data,
            "total": total
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo datos de ingresos: {str(e)}"
        )


# ============================================
# ENDPOINT 13: ANALYTICS - PIE CHART EGRESOS
# ============================================
@router.get("/analytics/pie-egresos")
async def pie_egresos(
    mes: Optional[str] = Query(None, description="Mes en formato YYYY-MM (opcional)"),
    period: Optional[str] = Query(None, description="Alias de mes (formato YYYY-MM, opcional)"),
    db: Session = Depends(get_db)
):
    """
    Retorna datos para pie chart de egresos por categoría.
    Usa la misma fuente de verdad que /api/reportes (generar_reporte_ejecutivo).

    Parámetros:
    - mes: Filtro opcional por mes (YYYY-MM)
    - period: Alias de mes (formato YYYY-MM, opcional)

    Retorna:
    - status: "success"
    - data: Lista de objetos {label, value}
    - total: Total de egresos (positivo)
    """
    try:
        mes = period or mes
        # Usar la misma fuente de verdad que /api/reportes
        reporte = generar_reporte_ejecutivo(db, mes)

        # Extraer desglose de egresos del reporte
        desglose_egresos = reporte.get("desglose_egresos", [])

        # Formatear para charts.js
        data = [
            {
                "label": item["categoria"],
                "value": item["monto"]  # Ya viene en valor absoluto del reporte
            }
            for item in desglose_egresos
        ]

        # Total de egresos del reporte (siempre positivo)
        total = reporte["saldos"]["egresos_total"]

        return JSONResponse({
            "status": "success",
            "data": data,
            "total": total
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo datos de egresos: {str(e)}"
        )


# ============================================
# ENDPOINT 14: ANALYTICS - LINE CHART FLUJO DIARIO
# ============================================
@router.get("/analytics/flujo-diario")
async def flujo_diario(
    mes: str = Query(..., description="Mes en formato YYYY-MM"),
    period: Optional[str] = Query(None, description="Alias de mes (formato YYYY-MM)"),
    db: Session = Depends(get_db)
):
    """
    Retorna datos para line chart de flujo de caja diario.
    Usa la misma lógica que /api/reportes (basada en signo del monto).

    Parámetros:
    - mes: Mes requerido en formato YYYY-MM
    - period: Alias de mes (formato YYYY-MM)

    Retorna:
    - dias: Lista de fechas
    - ingresos: Lista de ingresos diarios (positivos)
    - egresos: Lista de egresos diarios (valor absoluto)
    - neto: Lista de flujo neto diario
    """
    try:
        mes = period or mes
        # Query para ingresos agrupados por día (monto > 0)
        ingresos_query = db.query(
            func.date(Movimiento.fecha).label('dia'),
            func.sum(Movimiento.monto).label('total')
        ).filter(
            Movimiento.monto > 0,
            func.strftime('%Y-%m', Movimiento.fecha) == mes
        ).group_by(func.date(Movimiento.fecha)).all()

        # Query para egresos agrupados por día (monto < 0)
        egresos_query = db.query(
            func.date(Movimiento.fecha).label('dia'),
            func.sum(Movimiento.monto).label('total')
        ).filter(
            Movimiento.monto < 0,
            func.strftime('%Y-%m', Movimiento.fecha) == mes
        ).group_by(func.date(Movimiento.fecha)).all()

        # Crear diccionarios para mapeo rápido
        ingresos_dict = {str(i[0]): float(i[1]) for i in ingresos_query}
        egresos_dict = {str(e[0]): abs(float(e[1])) for e in egresos_query}

        # Obtener todos los días únicos
        todos_dias = sorted(set(ingresos_dict.keys()) | set(egresos_dict.keys()))

        # Construir listas paralelas
        dias = []
        ingresos = []
        egresos = []
        neto = []

        for dia in todos_dias:
            ing = ingresos_dict.get(dia, 0)
            egr = egresos_dict.get(dia, 0)

            dias.append(dia)
            ingresos.append(ing)
            egresos.append(egr)
            neto.append(ing - egr)

        return JSONResponse({
            "dias": dias,
            "ingresos": ingresos,
            "egresos": egresos,
            "neto": neto,
            "mes": mes,
            "total_ingresos": sum(ingresos),
            "total_egresos": sum(egresos),
            "balance": sum(ingresos) - sum(egresos)
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo flujo diario: {str(e)}"
        )


# ============================================
# ETAPA 7: EXPORTACIÓN PDF Y EXCEL
# ============================================

# Importar endpoints de exportación
from backend.api.exportacion import exportar_reporte_pdf, exportar_movimientos_excel, exportar_excel_ejecutivo

@router.get("/reportes/pdf")
async def get_reporte_pdf(
    mes: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Exportar reporte ejecutivo a PDF"""
    mes = period or mes
    return await exportar_reporte_pdf(mes, db)


@router.get("/reportes/excel")
async def get_excel_ejecutivo(
    mes: str = Query(...),
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Exportar Excel Ejecutivo con 5 hojas (ETAPA 7.B)"""
    mes = period or mes
    return await exportar_excel_ejecutivo(mes, db)


@router.get("/movimientos/excel")
async def get_movimientos_excel(
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    categoria: Optional[str] = Query(None),
    mes: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Exportar movimientos a Excel"""
    mes = period or mes
    return await exportar_movimientos_excel(fecha_desde, fecha_hasta, categoria, mes, db)


# ============================================
# ETAPA 4: REGLAS APRENDIBLES
# ============================================

from pydantic import BaseModel
from backend.models.regla_categorizacion import ReglaCategorizacion
from backend.core.reglas_aprendidas import (
    normalizar_texto,
    generar_patron_desde_descripcion,
    obtener_o_crear_regla
)


class ReglaRequest(BaseModel):
    """Request body para crear/actualizar regla"""
    patron: str
    categoria: str
    subcategoria: str


@router.post("/reglas")
async def crear_regla(
    regla_data: ReglaRequest,
    db: Session = Depends(get_db)
):
    """
    Crea o actualiza una regla de categorización aprendida.

    Si existe una regla con el mismo patrón:
    - Incrementa veces_usada
    - Incrementa confianza (máximo 100)
    - Actualiza categoría/subcategoría (la última corrección manda)

    Si no existe:
    - Crea nueva regla con confianza=50, veces_usada=1
    """
    try:
        # Normalizar patrón
        patron_normalizado = normalizar_texto(regla_data.patron)

        if not patron_normalizado:
            raise HTTPException(
                status_code=400,
                detail="El patrón no puede estar vacío"
            )

        # Obtener o crear regla
        regla = obtener_o_crear_regla(
            patron=patron_normalizado,
            categoria=regla_data.categoria,
            subcategoria=regla_data.subcategoria,
            db=db
        )

        return JSONResponse({
            "status": "success",
            "mensaje": "Regla guardada exitosamente",
            "regla": {
                "id": regla.id,
                "patron": regla.patron,
                "categoria": regla.categoria,
                "subcategoria": regla.subcategoria,
                "confianza": regla.confianza,
                "veces_usada": regla.veces_usada,
                "created_at": regla.created_at.isoformat() if regla.created_at else None
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error guardando regla: {str(e)}"
        )


@router.get("/reglas")
async def listar_reglas(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las reglas aprendidas, ordenadas por confianza y uso.

    Parámetros:
    - categoria: Filtro opcional por categoría (INGRESOS, EGRESOS, etc.)

    Retorna:
    - Lista de reglas con todos sus campos
    """
    try:
        query = db.query(ReglaCategorizacion)

        # Filtro opcional por categoría
        if categoria:
            query = query.filter(ReglaCategorizacion.categoria == categoria.upper())

        # Ordenar por confianza y uso
        reglas = query.order_by(
            ReglaCategorizacion.confianza.desc(),
            ReglaCategorizacion.veces_usada.desc()
        ).all()

        return JSONResponse({
            "status": "success",
            "total": len(reglas),
            "reglas": [
                {
                    "id": r.id,
                    "patron": r.patron,
                    "categoria": r.categoria,
                    "subcategoria": r.subcategoria,
                    "confianza": r.confianza,
                    "veces_usada": r.veces_usada,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in reglas
            ]
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listando reglas: {str(e)}"
        )


# ============================================
# ENDPOINT: PERIODOS DISPONIBLES (PARA SELECTOR DINÁMICO)
# ============================================

@router.get("/periodos")
async def obtener_periodos(db: Session = Depends(get_db)):
    """
    Obtiene todos los períodos (YYYY-MM) disponibles en la BD,
    agrupados por año, ordenados DESC.

    Retorna:
    {
      "periodos": {
        "2025": ["2025-11", "2025-10", "2025-09", "2025-08"],
        "2024": ["2024-12", "2024-11"]
      }
    }
    """
    try:
        # Obtener todos los meses únicos (formato YYYY-MM) de movimientos
        meses_query = db.query(
            func.strftime('%Y-%m', Movimiento.fecha).label('periodo')
        ).distinct().order_by(
            func.strftime('%Y-%m', Movimiento.fecha).desc()
        ).all()

        # Extraer periodos como strings
        periodos_list = [m[0] for m in meses_query if m[0]]

        # Agrupar por año
        periodos_agrupados = {}
        for periodo in periodos_list:
            year = periodo.split('-')[0]
            if year not in periodos_agrupados:
                periodos_agrupados[year] = []
            periodos_agrupados[year].append(periodo)

        return JSONResponse({
            "status": "success",
            "periodos": periodos_agrupados
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo periodos: {str(e)}"
        )


# ============================================
# ENDPOINT: METADATA (Vista específica de metadata con filtros extendidos)
# ============================================
@router.get("/metadata")
async def obtener_metadata(
    mes: Optional[str] = None,
    batch_id: Optional[int] = None,
    q: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    con_metadata: bool = False,
    con_debin: bool = False,
    con_documento: bool = False,
    con_nombre: bool = False,
    solo_ingresos: bool = False,
    solo_egresos: bool = False,
    db: Session = Depends(get_db)
):
    """
    Obtiene movimientos con sus campos de metadata para la vista /metadata

    Query params:
    - mes: "YYYY-MM" | "all" (opcional, default todos los movimientos)
    - batch_id: ID del batch para filtrar por archivo importado
    - q: búsqueda libre (case-insensitive) en múltiples campos
    - limit: cantidad máxima de resultados (default 200)
    - offset: offset para paginación (default 0)
    - con_metadata: solo movimientos con al menos un campo de metadata
    - con_debin: solo movimientos DEBIN
    - con_documento: solo con documento (CUIT/CUIL/DNI)
    - con_nombre: solo con nombre de persona/entidad
    - solo_ingresos: solo movimientos con monto > 0 (INGRESOS)
    - solo_egresos: solo movimientos con monto < 0 (EGRESOS)

    Returns:
        JSON con items, total, limit y offset
    """
    try:
        # Log para debugging de sincronización
        print(f"[metadata] mes recibido = {mes}, batch_id={batch_id}, q={q}")

        # Query base
        query = db.query(Movimiento)

        # Filtro por mes
        if mes and mes != "all":
            # Validar formato mes
            if not re.match(r'^\d{4}-\d{2}$', mes):
                raise HTTPException(status_code=400, detail="Formato de mes inválido. Use YYYY-MM o 'all'")

            year, month = mes.split('-')
            query = query.filter(
                extract('year', Movimiento.fecha) == int(year),
                extract('month', Movimiento.fecha) == int(month)
            )

        # Filtro por batch/archivo
        if batch_id:
            query = query.filter(Movimiento.batch_id == batch_id)

        # Búsqueda libre (q) - buscar en múltiples campos
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                (Movimiento.descripcion.ilike(search_term)) |
                (Movimiento.persona_nombre.ilike(search_term)) |
                (Movimiento.documento.ilike(search_term)) |
                (Movimiento.debin_id.ilike(search_term)) |
                (Movimiento.cbu.ilike(search_term)) |
                (Movimiento.comercio.ilike(search_term)) |
                (Movimiento.terminal.ilike(search_term)) |
                (Movimiento.referencia.ilike(search_term))
            )

        # Aplicar filtros de metadata
        if con_metadata:
            # Al menos UNO de estos campos debe ser no nulo/no vacío
            query = query.filter(
                (Movimiento.persona_nombre.isnot(None)) |
                (Movimiento.documento.isnot(None)) |
                (Movimiento.debin_id.isnot(None)) |
                (Movimiento.cbu.isnot(None)) |
                (Movimiento.comercio.isnot(None)) |
                (Movimiento.terminal.isnot(None)) |
                (Movimiento.referencia.isnot(None))
            )

        if con_debin:
            query = query.filter(
                (Movimiento.es_debin == True) |
                (Movimiento.debin_id.isnot(None))
            )

        if con_documento:
            query = query.filter(
                Movimiento.documento.isnot(None),
                Movimiento.documento != ""
            )

        if con_nombre:
            query = query.filter(
                Movimiento.persona_nombre.isnot(None),
                Movimiento.persona_nombre != ""
            )

        # Filtro por tipo de movimiento (INGRESO/EGRESO)
        if solo_ingresos:
            query = query.filter(Movimiento.monto > 0)

        if solo_egresos:
            query = query.filter(Movimiento.monto < 0)

        # Contar total (antes de limit/offset)
        total = query.count()

        # Ordenar por fecha DESC, id DESC (estabilidad)
        movimientos = query.order_by(Movimiento.fecha.desc(), Movimiento.id.desc()).limit(limit).offset(offset).all()

        # Serializar movimientos con todos los campos de metadata
        items = []
        for mov in movimientos:
            items.append({
                'id': mov.id,
                'fecha': mov.fecha.isoformat() if mov.fecha else None,
                'monto': mov.monto,
                'descripcion': mov.descripcion,
                'categoria': mov.categoria,
                'subcategoria': mov.subcategoria,
                'confianza': mov.confianza_porcentaje,  # Puede ser None
                'batch_id': mov.batch_id,
                # Metadata (8 campos)
                'nombre': mov.persona_nombre,
                'documento': mov.documento,
                'es_debin': mov.es_debin,
                'debin_id': mov.debin_id,
                'cbu': mov.cbu,
                'comercio': mov.comercio,
                'terminal': mov.terminal,
                'referencia': mov.referencia
            })

        # Calcular estadísticas de confianza sobre el query completo (sin paginación)
        stats = {}
        try:
            # Obtener todos los movimientos del query filtrado (sin limit/offset) para stats
            all_movimientos = query.all()

            if all_movimientos:
                # Valores de confianza no nulos
                confianzas_validas = [m.confianza_porcentaje for m in all_movimientos if m.confianza_porcentaje is not None]

                # Confianza promedio
                if confianzas_validas:
                    stats['confianza_promedio'] = round(sum(confianzas_validas) / len(confianzas_validas), 1)
                else:
                    stats['confianza_promedio'] = None

                # Contadores
                stats['sin_confianza_count'] = sum(1 for m in all_movimientos if m.confianza_porcentaje is None)
                stats['confianza_cero_count'] = sum(1 for m in all_movimientos if m.confianza_porcentaje == 0)
                stats['confianza_baja_count'] = sum(1 for m in all_movimientos if m.confianza_porcentaje is not None and 0 < m.confianza_porcentaje < 50)
                stats['total_filtrado'] = total
            else:
                stats['confianza_promedio'] = None
                stats['sin_confianza_count'] = 0
                stats['confianza_cero_count'] = 0
                stats['confianza_baja_count'] = 0
                stats['total_filtrado'] = 0
        except Exception as e:
            # Si falla el cálculo de stats, retornar valores por defecto
            print(f"[metadata] Error calculando stats: {e}")
            stats = {
                'confianza_promedio': None,
                'sin_confianza_count': 0,
                'confianza_cero_count': 0,
                'confianza_baja_count': 0,
                'total_filtrado': total
            }

        return JSONResponse({
            'status': 'success',
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset,
            'stats': stats
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo metadata: {str(e)}"
        )


# ============================================
# ENDPOINT: APLICAR REGLAS MASIVAMENTE
# ============================================
@router.post("/reglas/aplicar")
async def aplicar_reglas_masivas(
    mes: Optional[str] = None,
    batch_id: Optional[int] = None,
    solo_sin_categoria: bool = False,
    solo_confianza_menor_a: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Aplica reglas de categorización masivamente según filtros.

    Parámetros:
    - mes: Filtrar por mes (formato YYYY-MM) o "all" para todos
    - batch_id: Filtrar por batch específico
    - solo_sin_categoria: Solo recategorizar movimientos sin categoría
    - solo_confianza_menor_a: Solo recategorizar si confianza < valor (ej: 50)

    Retorna:
    - status: "success" o "error"
    - evaluados: Total de movimientos evaluados
    - actualizados: Movimientos efectivamente recategorizados
    - estadisticas: Breakdown por categoría
    """
    try:
        from backend.core.categorizador_cascada import CategorizadorCascada
        from backend.core.reglas_aprendidas import buscar_regla_aplicable, aplicar_regla_a_movimiento

        # Construir query base
        query = db.query(Movimiento)

        # Filtro por mes
        if mes and mes != "all":
            if not re.match(r'^\d{4}-\d{2}$', mes):
                raise HTTPException(
                    status_code=400,
                    detail="Formato de mes inválido. Use YYYY-MM o 'all'"
                )
            year, month = mes.split('-')
            query = query.filter(
                extract('year', Movimiento.fecha) == int(year),
                extract('month', Movimiento.fecha) == int(month)
            )

        # Filtro por batch
        if batch_id:
            query = query.filter(Movimiento.batch_id == batch_id)

        # Filtro por sin categoría
        if solo_sin_categoria:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Movimiento.categoria == None,
                    Movimiento.categoria == "SIN_CATEGORIA",
                    Movimiento.categoria == ""
                )
            )

        # Filtro por confianza baja
        if solo_confianza_menor_a is not None:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Movimiento.confianza_porcentaje == None,
                    Movimiento.confianza_porcentaje < solo_confianza_menor_a
                )
            )

        # Obtener movimientos a procesar
        movimientos = query.all()

        if not movimientos:
            return JSONResponse({
                'status': 'success',
                'mensaje': 'No hay movimientos que cumplan los criterios de filtrado',
                'evaluados': 0,
                'actualizados': 0,
                'estadisticas': {}
            })

        # Inicializar motor de categorización
        motor = CategorizadorCascada()

        # Estadísticas
        evaluados = 0
        actualizados = 0
        por_regla_aprendida = 0
        por_motor_cascada = 0
        estadisticas_categorias = {}

        # Procesar cada movimiento
        for mov in movimientos:
            evaluados += 1
            categoria_anterior = mov.categoria

            # SKIP: NO PISAR categorizaciones manuales
            if hasattr(mov, 'confianza_fuente') and mov.confianza_fuente == "manual":
                # Mantener categorización manual intacta
                key = f"{mov.categoria}:{mov.subcategoria}"
                if key not in estadisticas_categorias:
                    estadisticas_categorias[key] = {
                        'categoria': mov.categoria,
                        'subcategoria': mov.subcategoria,
                        'count': 0
                    }
                estadisticas_categorias[key]['count'] += 1
                continue

            # PASO 1: Intentar regla aprendida
            regla_aplicable = buscar_regla_aplicable(mov.descripcion or "", db)

            if regla_aplicable:
                # Aplicar regla aprendida
                aplicar_regla_a_movimiento(regla_aplicable, mov, db)
                por_regla_aprendida += 1
                actualizados += 1

                # Setear confianza y fuente si no está seteada
                if not mov.confianza_porcentaje or mov.confianza_porcentaje < 95:
                    mov.confianza_porcentaje = 95

                if hasattr(mov, 'confianza_fuente'):
                    mov.confianza_fuente = "regla_aprendida"
            else:
                # PASO 2: Aplicar motor cascada
                resultado = motor.categorizar_cascada(
                    concepto=mov.descripcion or "",
                    detalle=mov.descripcion or "",
                    monto=mov.monto
                )

                # Solo actualizar si cambió algo
                if (mov.categoria != resultado.categoria or
                    mov.subcategoria != resultado.subcategoria or
                    mov.confianza_porcentaje != resultado.confianza):

                    mov.categoria = resultado.categoria
                    mov.subcategoria = resultado.subcategoria
                    mov.confianza_porcentaje = resultado.confianza

                    # Setear confianza_fuente
                    if hasattr(mov, 'confianza_fuente'):
                        mov.confianza_fuente = "cascada"

                    por_motor_cascada += 1
                    actualizados += 1

            # FIX CRÍTICO: Si el movimiento tiene categoría/subcategoría pero confianza 0 o NULL
            if mov.categoria and mov.subcategoria and mov.categoria != "SIN_CATEGORIA":
                if not mov.confianza_porcentaje or mov.confianza_porcentaje == 0:
                    # Setear confianza según la fuente actual
                    if hasattr(mov, 'confianza_fuente'):
                        if mov.confianza_fuente == "regla_aprendida":
                            mov.confianza_porcentaje = 95
                        elif mov.confianza_fuente == "cascada":
                            mov.confianza_porcentaje = 70
                        elif mov.confianza_fuente == "manual":
                            mov.confianza_porcentaje = 100
                        else:
                            mov.confianza_porcentaje = 60
                            mov.confianza_fuente = "sin_fuente"
                    else:
                        # Si no tiene confianza_fuente (modelo viejo), setear default
                        mov.confianza_porcentaje = 60

            # Actualizar estadísticas
            key = f"{mov.categoria}:{mov.subcategoria}"
            if key not in estadisticas_categorias:
                estadisticas_categorias[key] = {
                    'categoria': mov.categoria,
                    'subcategoria': mov.subcategoria,
                    'count': 0
                }
            estadisticas_categorias[key]['count'] += 1

        # Commit de cambios
        db.commit()

        # Ordenar estadísticas por count
        stats_list = sorted(
            estadisticas_categorias.values(),
            key=lambda x: x['count'],
            reverse=True
        )

        return JSONResponse({
            'status': 'success',
            'mensaje': f'Reglas aplicadas exitosamente: {actualizados} movimientos actualizados',
            'evaluados': evaluados,
            'actualizados': actualizados,
            'por_regla_aprendida': por_regla_aprendida,
            'por_motor_cascada': por_motor_cascada,
            'porcentaje_actualizados': round((actualizados / evaluados * 100) if evaluados > 0 else 0, 2),
            'estadisticas': stats_list[:10]  # Top 10
        })

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error aplicando reglas masivas: {str(e)}"
        )


# ============================================
# ENDPOINTS: CATÁLOGO DE CATEGORÍAS (READ-ONLY MVP)
# ============================================

@router.get("/config/categorias")
def api_config_categorias():
    """
    Devuelve el catálogo completo de categorías desde JSON

    Returns:
        JSON con version, updated_at, y lista de categorías con subcategorías
    """
    try:
        catalog = load_catalog()
        return catalog
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cargando catálogo de categorías: {str(e)}"
        )


@router.get("/categorias/tree")
def api_categorias_tree():
    """
    Devuelve el árbol jerárquico de categorías y subcategorías

    Returns:
        JSON con lista de categorías, cada una con sus subcategorías anidadas

    Example:
        {
          "categorias": [
            {
              "key": "IMPUESTOS",
              "label": "Impuestos",
              "tipo": "EGRESO",
              "icon": "🏛️",
              "color": "#f59e0b",
              "subcategorias": [
                {"key": "Impuestos - IVA", "label": "IVA"},
                ...
              ]
            },
            ...
          ]
        }
    """
    try:
        tree = get_tree()
        return {"categorias": tree}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo árbol de categorías: {str(e)}"
        )
