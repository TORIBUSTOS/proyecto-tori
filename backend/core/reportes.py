"""
Modulo de generacion de reportes financieros
Genera reportes ejecutivos con KPIs y analisis de movimientos
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.models.movimiento import Movimiento
from dateutil.relativedelta import relativedelta


def generar_reporte_ejecutivo(db: Session, mes: Optional[str] = None) -> dict:
    """
    Genera un reporte ejecutivo financiero completo para un mes especifico

    Args:
        db: Sesion de base de datos SQLAlchemy
        mes: Mes en formato "YYYY-MM". Si None, usa mes actual.

    Returns:
        dict con:
            - periodo: "YYYY-MM"
            - kpis: {ingresos_total, egresos_total, saldo_neto, cantidad_movimientos, categorias_activas}
            - saldos: {saldo_inicial, ingresos_total, egresos_total, variacion, saldo_final}
            - clasificacion: {total_movimientos, clasificados, sin_clasificar, pct_clasificados}
            - desglose_ingresos: lista completa de ingresos por categoria
            - desglose_egresos: lista completa de egresos por categoria
            - top_egresos_por_categoria: top 5 categorias con mayor egreso (compatibilidad)
            - ultimos_movimientos: ultimos 10 movimientos del periodo
            - comparacion_mes_anterior: comparacion con mes anterior
    """

    # 1. Determinar periodo
    if mes:
        # Parsear formato "YYYY-MM"
        year, month = map(int, mes.split("-"))
        fecha_inicio = date(year, month, 1)
    else:
        # Usar mes actual
        hoy = datetime.now()
        fecha_inicio = date(hoy.year, hoy.month, 1)

    # Calcular fin del mes (inicio del mes siguiente)
    fecha_fin = fecha_inicio + relativedelta(months=1)

    # Formato del periodo para respuesta
    periodo = fecha_inicio.strftime("%Y-%m")

    # 2. Calcular KPIs del periodo
    # Filtro base: movimientos del mes
    query_mes = db.query(Movimiento).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin
        )
    )

    # Total ingresos (monto > 0)
    ingresos_total = db.query(func.sum(Movimiento.monto)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.monto > 0
        )
    ).scalar() or 0.0

    # Total egresos (abs de monto < 0)
    egresos_sum = db.query(func.sum(Movimiento.monto)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.monto < 0
        )
    ).scalar() or 0.0
    egresos_total = abs(egresos_sum)

    # Saldo neto (suma total)
    saldo_neto = db.query(func.sum(Movimiento.monto)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin
        )
    ).scalar() or 0.0

    # Cantidad de movimientos
    cantidad_movimientos = query_mes.count()

    # Categorias activas (excluyendo SIN_CATEGORIA)
    categorias_activas = db.query(func.count(func.distinct(Movimiento.categoria))).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.categoria.isnot(None),
            Movimiento.categoria != "",
            Movimiento.categoria != "SIN_CATEGORIA"
        )
    ).scalar() or 0

    # 3. Top 5 egresos por categoria
    top_egresos = db.query(
        Movimiento.categoria,
        func.sum(Movimiento.monto).label("total_egresos")
    ).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.monto < 0,
            Movimiento.categoria != "SIN_CATEGORIA"
        )
    ).group_by(
        Movimiento.categoria
    ).order_by(
        func.sum(Movimiento.monto).asc()  # Ordenar ascendente (mas negativo primero)
    ).limit(5).all()

    top_egresos_por_categoria = [
        {
            "categoria": cat,
            "total_egresos": abs(total)
        }
        for cat, total in top_egresos
    ]

    # 4. Ultimos 10 movimientos del periodo
    ultimos = query_mes.order_by(Movimiento.fecha.desc()).limit(10).all()

    ultimos_movimientos = [
        {
            "fecha": mov.fecha.isoformat(),
            "descripcion": mov.descripcion,
            "monto": mov.monto,
            "categoria": mov.categoria or "SIN_CATEGORIA"
        }
        for mov in ultimos
    ]

    # 5. SALDOS BANCARIOS (saldo_inicial, variacion, saldo_final)
    # Saldo inicial = saldo del PRIMER movimiento del mes
    # Saldo final = saldo del ÚLTIMO movimiento del mes

    # Buscar primer movimiento del periodo
    # Ordenar por: fecha ASC, saldo DESC (el saldo mas alto del dia es el primer movimiento)
    primer_mov = db.query(Movimiento).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.saldo.isnot(None)
        )
    ).order_by(Movimiento.fecha.asc(), Movimiento.saldo.desc()).first()

    # Buscar último movimiento del periodo
    # Ordenar por: fecha DESC, saldo ASC (el saldo mas bajo del dia es el ultimo movimiento)
    ultimo_mov = db.query(Movimiento).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.saldo.isnot(None)
        )
    ).order_by(Movimiento.fecha.desc(), Movimiento.saldo.asc()).first()

    if primer_mov and ultimo_mov:
        # Si el primer movimiento tiene saldo, el saldo inicial es: saldo_primer_mov - monto_primer_mov
        # Esto da el saldo ANTES de ejecutar el primer movimiento del mes
        saldo_inicial = primer_mov.saldo - primer_mov.monto
        saldo_final = ultimo_mov.saldo
        variacion = saldo_neto  # La variación es la suma de movimientos del periodo
    else:
        # Fallback: si no hay saldos, calcular sumando movimientos anteriores (método anterior)
        saldo_inicial = db.query(func.sum(Movimiento.monto)).filter(
            Movimiento.fecha < fecha_inicio
        ).scalar() or 0.0
        variacion = saldo_neto
        saldo_final = saldo_inicial + variacion

    # 6. CLASIFICACION (movimientos clasificados vs sin clasificar)
    # Total de movimientos ya lo tenemos en cantidad_movimientos

    # Movimientos clasificados (tienen categoria != SIN_CATEGORIA)
    clasificados = db.query(func.count(Movimiento.id)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.categoria.isnot(None),
            Movimiento.categoria != "",
            Movimiento.categoria != "SIN_CATEGORIA"
        )
    ).scalar() or 0

    # Sin clasificar
    sin_clasificar = cantidad_movimientos - clasificados

    # Porcentaje clasificados
    pct_clasificados = round((clasificados / cantidad_movimientos * 100), 2) if cantidad_movimientos > 0 else 0.0

    # 7. DESGLOSE INGRESOS COMPLETO (todas las categorias de ingresos)
    desglose_ingresos_query = db.query(
        Movimiento.categoria,
        func.sum(Movimiento.monto).label("total")
    ).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.monto > 0,
            Movimiento.categoria.isnot(None),
            Movimiento.categoria != "",
            Movimiento.categoria != "SIN_CATEGORIA"
        )
    ).group_by(
        Movimiento.categoria
    ).order_by(
        func.sum(Movimiento.monto).desc()
    ).all()

    desglose_ingresos = [
        {
            "categoria": cat,
            "monto": round(total, 2)
        }
        for cat, total in desglose_ingresos_query
    ]

    # 8. DESGLOSE EGRESOS COMPLETO (todas las categorias de egresos, no solo Top 5)
    desglose_egresos_query = db.query(
        Movimiento.categoria,
        func.sum(Movimiento.monto).label("total")
    ).filter(
        and_(
            Movimiento.fecha >= fecha_inicio,
            Movimiento.fecha < fecha_fin,
            Movimiento.monto < 0,
            Movimiento.categoria.isnot(None),
            Movimiento.categoria != "",
            Movimiento.categoria != "SIN_CATEGORIA"
        )
    ).group_by(
        Movimiento.categoria
    ).order_by(
        func.sum(Movimiento.monto).asc()  # Mas negativo primero
    ).all()

    desglose_egresos = [
        {
            "categoria": cat,
            "monto": round(abs(total), 2)
        }
        for cat, total in desglose_egresos_query
    ]

    # 9. Comparacion con mes anterior
    fecha_inicio_anterior = fecha_inicio - relativedelta(months=1)
    fecha_fin_anterior = fecha_inicio  # El inicio del mes actual es el fin del anterior

    # Ingresos mes anterior
    ingresos_total_anterior = db.query(func.sum(Movimiento.monto)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio_anterior,
            Movimiento.fecha < fecha_fin_anterior,
            Movimiento.monto > 0
        )
    ).scalar() or 0.0

    # Egresos mes anterior
    egresos_sum_anterior = db.query(func.sum(Movimiento.monto)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio_anterior,
            Movimiento.fecha < fecha_fin_anterior,
            Movimiento.monto < 0
        )
    ).scalar() or 0.0
    egresos_total_anterior = abs(egresos_sum_anterior)

    # Saldo neto mes anterior
    saldo_neto_anterior = db.query(func.sum(Movimiento.monto)).filter(
        and_(
            Movimiento.fecha >= fecha_inicio_anterior,
            Movimiento.fecha < fecha_fin_anterior
        )
    ).scalar() or 0.0

    # Calcular variacion porcentual
    variacion_saldo_pct = None
    if saldo_neto_anterior != 0:
        variacion_saldo_pct = round(
            ((saldo_neto - saldo_neto_anterior) / abs(saldo_neto_anterior)) * 100,
            2
        )

    # 10. Construir respuesta
    reporte = {
        "periodo": periodo,
        "kpis": {
            "ingresos_total": round(ingresos_total, 2),
            "egresos_total": round(egresos_total, 2),
            "saldo_neto": round(saldo_neto, 2),
            "cantidad_movimientos": cantidad_movimientos,
            "categorias_activas": categorias_activas
        },
        "saldos": {
            "saldo_inicial": round(saldo_inicial, 2),
            "ingresos_total": round(ingresos_total, 2),
            "egresos_total": round(egresos_total, 2),
            "variacion": round(variacion, 2),
            "saldo_final": round(saldo_final, 2)
        },
        "clasificacion": {
            "total_movimientos": cantidad_movimientos,
            "clasificados": clasificados,
            "sin_clasificar": sin_clasificar,
            "pct_clasificados": pct_clasificados
        },
        "desglose_ingresos": desglose_ingresos,
        "desglose_egresos": desglose_egresos,
        "top_egresos_por_categoria": top_egresos_por_categoria,  # Mantener para compatibilidad
        "ultimos_movimientos": ultimos_movimientos,
        "comparacion_mes_anterior": {
            "ingresos_total_anterior": round(ingresos_total_anterior, 2),
            "egresos_total_anterior": round(egresos_total_anterior, 2),
            "saldo_neto_anterior": round(saldo_neto_anterior, 2),
            "variacion_saldo_pct": variacion_saldo_pct
        }
    }

    return reporte
