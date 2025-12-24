"""
Categorización de movimientos (MVP+)
- Normaliza descripciones (tildes, mayúsculas, símbolos)
- Reglas por prioridad (primero específicas)
- Subcategorías sin cambiar DB: categoria = "CATEGORIA:SUB"
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

# Ajustá el import si tu modelo se llama distinto
from backend.models.movimiento import Movimiento


def _norm(s: str) -> str:
    """
    Normalización fuerte:
    - lowercase
    - sin tildes
    - espacios compactados
    - deja letras/números y algunos separadores
    """
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # reemplazar separadores comunes por espacio
    s = re.sub(r"[\-\_/|·•]+", " ", s)
    # quitar caracteres raros (dejamos letras/números/espacio)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    # compactar espacios
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass(frozen=True)
class Rule:
    cat: str                      # "ALIMENTACION"
    sub: Optional[str]            # "DELIVERY" (opcional)
    pattern: str                  # regex
    flags: int = re.IGNORECASE

    def compile(self) -> re.Pattern:
        return re.compile(self.pattern, self.flags)

    def label(self) -> str:
        return f"{self.cat}:{self.sub}" if self.sub else self.cat


# Reglas en ORDEN de prioridad (más específicas arriba)
# TIP: agregá marcas/merchants reales de tu banco acá.
RULES: List[Rule] = [
    # --- IMPUESTOS / COMISIONES (primero, son muy distintivos)
    Rule("IMPUESTOS", "DEBITOS_Y_CREDITOS", r"\bimpuesto\b.*\bdebitos?\b.*\bcreditos?\b|\bdebitos?\b.*\bcreditos?\b"),
    Rule("IMPUESTOS", "IVA", r"\biva\b"),
    Rule("COMISIONES", "MANTENIMIENTO", r"\bmantenimiento\b|\bcomision\b.*\bpaquete\b|\bpaquete\b.*\bservicio\b"),
    Rule("COMISIONES", "EXTRACCION", r"\bcomision\b.*\bcajero\b|\bfee\b.*\batm\b"),

    # --- TRANSFERENCIAS / INGRESOS
    Rule("INGRESOS", "SUELDO", r"\bsueldo\b|\bhaberes\b"),
    Rule("TRANSFERENCIAS", "DEPOSITO", r"\bdeposito\b|\bdep\b\b"),
    Rule("TRANSFERENCIAS", "TRANSFERENCIA", r"\btransferencia\b|\btrf\b|\btransf\b|\btef\b"),

    # --- ALIMENTACION
    Rule("ALIMENTACION", "DELIVERY", r"\bpedidos?ya\b|\brappi\b|\buber\s?eats\b|\bglovo\b"),
    Rule("ALIMENTACION", "SUPERMERCADO", r"\bcarrefour\b|\bcoto\b|\bjumbo\b|\bdia\b|\bvea\b|\bdisco\b|\bwalmart\b|\bchangomas\b|\bsupermercad"),
    Rule("ALIMENTACION", None, r"\brestaurante\b|\bparrilla\b|\bcomida\b|\bbar\b|\bcafe\b"),

    # --- TRANSPORTE
    Rule("TRANSPORTE", "COMBUSTIBLE", r"\bypf\b|\bshell\b|\baxion\b|\bpuma\b|\bcombustible\b|\bnafta\b|\bgasoil\b"),
    Rule("TRANSPORTE", "UBER_CABIFY", r"\buber\b|\bcabify\b|\bdidi\b"),
    Rule("TRANSPORTE", "PEAJES", r"\bpeaje\b|\btelepase\b|\bausa\b"),
    Rule("TRANSPORTE", "ESTACIONAMIENTO", r"\bestacionamiento\b|\bparking\b"),

    # --- SALUD
    Rule("SALUD", "FARMACIA", r"\bfarmacia\b|\bfarmacity\b|\bsimilares\b|\bdr\s?ahorro\b|\bfarma\b"),
    Rule("SALUD", "PREPAGA", r"\bosde\b|\bswiss\b|\bgaleno\b|\bmedicus\b|\bomint\b"),
    Rule("SALUD", None, r"\bclinica\b|\bmedic\b|\bconsultorio\b|\bhospital\b"),

    # --- HOGAR / SERVICIOS
    Rule("HOGAR_SERVICIOS", "ALQUILER", r"\balquiler\b"),
    Rule("HOGAR_SERVICIOS", "EXPENSAS", r"\bexpensas\b"),
    Rule("HOGAR_SERVICIOS", "LUZ", r"\bedesur\b|\bedenor\b|\bluz\b|\belectric"),
    Rule("HOGAR_SERVICIOS", "GAS", r"\bmetrogas\b|\bgas\b"),
    Rule("HOGAR_SERVICIOS", "AGUA", r"\baySA\b|\baysa\b|\bagua\b"),
    Rule("HOGAR_SERVICIOS", "INTERNET_TV", r"\bpersonal\b|\bflow\b|\btelecentro\b|\bmovistar\b|\bclaro\b|\binternet\b|\bfibra\b"),

    # --- SUSCRIPCIONES / DIGITAL
    Rule("SUSCRIPCIONES", "STREAMING", r"\bnetflix\b|\bspotify\b|\bdisney\b|\bhbo\b|\bprime\b|\byoutube\b"),
    Rule("DIGITAL", "MERCADO_LIBRE", r"\bmercado\s?libre\b|\bmp\b|\bmercadopago\b|\bmpago\b"),
    Rule("DIGITAL", "TIENDA_APP", r"\bgoogle\b.*\bplay\b|\bapple\b.*\bcom\b|\bapp\s?store\b"),

    # --- RETIROS / EFECTIVO
    Rule("EFECTIVO", "EXTRACCION", r"\bextraccion\b|\bcajero\b|\batm\b"),

    # --- DEFAULT (al final)
    Rule("OTROS", None, r".*"),
]

# Compilamos una vez
_COMPILED: List[Tuple[Rule, re.Pattern]] = [(r, r.compile()) for r in RULES]


def _pick_categoria(descripcion: str) -> Tuple[str, str]:
    """
    Devuelve (categoria_final, regla_label)
    categoria_final puede incluir subcategoría: "ALIMENTACION:DELIVERY"
    """
    text = _norm(descripcion)
    for rule, rx in _COMPILED:
        if rx.search(text):
            return rule.label(), rule.label()
    return "OTROS", "OTROS"


def categorizar_movimientos(db: Session, solo_sin_categoria: bool = True) -> Dict[str, Any]:
    """
    Categoriza movimientos en DB.
    - si solo_sin_categoria=True: solo procesa categoria NULL o 'SIN_CATEGORIA'
    """
    q = db.query(Movimiento)
    if solo_sin_categoria:
        q = q.filter(or_(Movimiento.categoria == None, Movimiento.categoria == "SIN_CATEGORIA"))

    movs: List[Movimiento] = q.all()

    procesados = 0
    categorizados = 0
    por_categoria: Dict[str, int] = {}
    por_regla: Dict[str, int] = {}

    for m in movs:
        procesados += 1
        categoria_final, regla = _pick_categoria(m.descripcion or "")
        m.categoria = categoria_final
        categorizados += 1
        por_categoria[categoria_final] = por_categoria.get(categoria_final, 0) + 1
        por_regla[regla] = por_regla.get(regla, 0) + 1

    db.commit()

    # resumen ordenado
    categorias_distintas = sorted(por_categoria.keys())
    top_categorias = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "procesados": procesados,
        "categorizados": categorizados,
        "categorias_distintas": categorias_distintas,
        "top_categorias": top_categorias,
        "top_reglas": sorted(por_regla.items(), key=lambda x: x[1], reverse=True)[:10],
        "nota": "Subcategorías guardadas como 'CATEGORIA:SUB' en el campo categoria",
    }
