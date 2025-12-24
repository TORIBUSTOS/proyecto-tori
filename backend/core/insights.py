"""
TORO Investment Manager - Motor de Insights Financieros/Operativos
Genera lecturas estratégicas del período basadas en datos reales.

IMPORTANTE:
- Los insights describen PATRONES del negocio/operación financiera
- NO describen el estado del plan de paridad o roadmap
- Lenguaje humano, accionable, sin juicios de valor
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.movimiento import Movimiento


class Insight:
    """Representa un insight financiero/operativo"""

    def __init__(self, lens: str, title: str, message: str, action: str):
        self.lens = lens  # Categoría interna (NO visible en UI)
        self.title = title
        self.message = message
        self.action = action

    def to_dict(self) -> Dict[str, str]:
        return {
            "lens": self.lens,
            "title": self.title,
            "message": self.message,
            "action": self.action
        }


def generar_insights(reporte: Dict[str, Any], db: Session, mes: Optional[str] = None) -> List[Insight]:
    """
    Genera insights financieros/operativos basados en el reporte ejecutivo y movimientos.

    Args:
        reporte: Reporte ejecutivo del mes (de generar_reporte_ejecutivo)
        db: Sesión de base de datos
        mes: Mes en formato YYYY-MM (opcional)

    Returns:
        Lista de insights (máximo 7)
    """
    insights = []

    # 1. Movimientos sin clasificar
    clasificacion = reporte.get("clasificacion", {})
    sin_clasificar = clasificacion.get("sin_clasificar", 0)
    total_movimientos = clasificacion.get("total_movimientos", 0)

    if sin_clasificar > 0 and total_movimientos > 0:
        pct = (sin_clasificar / total_movimientos) * 100
        if pct >= 10:  # Más del 10% sin clasificar
            insights.append(Insight(
                lens="clasificacion",
                title="Movimientos sin clasificar",
                message=f"Se detectaron {sin_clasificar} movimientos sin categoría ({pct:.0f}% del total).",
                action="Corregirlos para mejorar reportes y automatismos."
            ))

    # 2. Concentración de egresos en una categoría
    desglose_egresos = reporte.get("desglose_egresos", [])
    if len(desglose_egresos) > 1:
        total_egresos = sum(abs(item["monto"]) for item in desglose_egresos)
        if total_egresos > 0:
            for item in desglose_egresos:
                pct = (abs(item["monto"]) / total_egresos) * 100
                if pct >= 40:  # Una categoría concentra más del 40%
                    insights.append(Insight(
                        lens="concentracion",
                        title="Concentración de egresos",
                        message=f"La categoría '{item['categoria']}' concentra {pct:.0f}% del gasto del mes.",
                        action="Revisar si es un gasto recurrente o excepcional."
                    ))
                    break  # Solo reportar la primera

    # 3. Balance negativo del mes
    saldos = reporte.get("saldos", {})
    variacion = saldos.get("variacion", 0)

    if variacion < 0:
        insights.append(Insight(
            lens="flujo",
            title="Flujo de caja negativo",
            message=f"El mes cerró con una variación negativa de ${abs(variacion):,.2f}.",
            action="Evaluar si es estacional o requiere ajustes en egresos."
        ))

    # 4. Detectar categorías nuevas (con pocos movimientos)
    if mes:
        # Buscar categorías con exactamente 1 movimiento en el mes
        query = db.query(
            Movimiento.categoria,
            func.count(Movimiento.id).label('count')
        ).filter(
            func.strftime('%Y-%m', Movimiento.fecha) == mes,
            Movimiento.categoria != "SIN_CATEGORIA"
        ).group_by(Movimiento.categoria)

        categorias_raras = [r for r in query.all() if r.count == 1]

        if categorias_raras:
            cat_nombre = categorias_raras[0].categoria
            insights.append(Insight(
                lens="operacion",
                title="Movimiento único detectado",
                message=f"La categoría '{cat_nombre}' tiene solo 1 movimiento en el mes.",
                action="Verificar si es un gasto excepcional o debe reclasificarse."
            ))

    # 5. Top prestador domina egresos
    top_egresos = reporte.get("top_egresos_por_categoria", [])
    if top_egresos:
        top = top_egresos[0]
        total_egresos = sum(abs(item["total_egresos"]) for item in top_egresos)
        if total_egresos > 0:
            pct = (abs(top["total_egresos"]) / total_egresos) * 100
            if pct >= 30:  # El top concentra más del 30%
                insights.append(Insight(
                    lens="prestadores",
                    title="Concentración en top categoría",
                    message=f"'{top['categoria']}' representa {pct:.0f}% de los egresos principales.",
                    action="Evaluar dependencia operativa o contractual."
                ))

    # 6. Comparación con mes anterior (crecimiento o caída significativos)
    comparacion = reporte.get("comparacion_mes_anterior", {})
    var_saldo_pct = comparacion.get("variacion_saldo_pct")

    if var_saldo_pct is not None:
        if var_saldo_pct >= 50:  # Crecimiento >50%
            insights.append(Insight(
                lens="tendencia",
                title="Crecimiento significativo",
                message=f"El saldo creció {var_saldo_pct:.0f}% respecto al mes anterior.",
                action="Identificar drivers del crecimiento para replicar patrón."
            ))
        elif var_saldo_pct <= -50:  # Caída >50%
            insights.append(Insight(
                lens="tendencia",
                title="Caída significativa",
                message=f"El saldo cayó {abs(var_saldo_pct):.0f}% respecto al mes anterior.",
                action="Analizar causas y evaluar medidas correctivas."
            ))

    # 7. Ingresos concentrados en una fuente
    desglose_ingresos = reporte.get("desglose_ingresos", [])
    if len(desglose_ingresos) > 1:
        total_ingresos = sum(item["monto"] for item in desglose_ingresos)
        if total_ingresos > 0:
            for item in desglose_ingresos:
                pct = (item["monto"] / total_ingresos) * 100
                if pct >= 70:  # Una fuente concentra más del 70%
                    insights.append(Insight(
                        lens="ingresos",
                        title="Concentración de ingresos",
                        message=f"'{item['categoria']}' representa {pct:.0f}% de los ingresos totales.",
                        action="Diversificar fuentes para reducir riesgo operativo."
                    ))
                    break

    # Limitar a máximo 7 insights (según especificación)
    return insights[:7]
