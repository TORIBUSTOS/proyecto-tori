"""
Motor de Categorización en Cascada v2.0 - Sistema TORO Web

Sistema de clasificación de 2 niveles:
1. Nivel 1 (Concepto): Categoría principal + subcategoría base
2. Nivel 2 (Detalle): Refinamiento de subcategoría según detalle

Basado en el ClasificadorCascada del CLI v2.0.0
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.models.movimiento import Movimiento


# ============================================================================
# NORMALIZACIÓN DE TEXTO
# ============================================================================

def normalize_text(texto: str) -> str:
    """
    Normalización de texto para comparación (función pública exportable):
    - Uppercase (cambiado desde lowercase para mejor detección)
    - Sin tildes (áéíóúüñ -> AEIOUUN)
    - Sin caracteres especiales
    - Espacios compactados
    - Trim

    Args:
        texto: Texto a normalizar

    Returns:
        Texto normalizado en MAYÚSCULAS
    """
    if texto is None:
        return ""

    # Uppercase y strip (cambiado a uppercase para reglas IVA/DB-CR)
    texto = str(texto).strip().upper()

    # Remover tildes
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))

    # Reemplazar separadores por espacio
    texto = re.sub(r"[\-\_/|·•]+", " ", texto)

    # Quitar caracteres especiales (dejar solo letras, números, espacio)
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)

    # Compactar espacios múltiples
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def _norm(texto: str) -> str:
    """
    Wrapper interno para mantener compatibilidad con código existente.
    Retorna lowercase para compatibilidad con reglas actuales.
    """
    if texto is None:
        return ""

    # Usar normalize_text y convertir a lowercase para compatibilidad
    return normalize_text(texto).lower()


# ============================================================================
# CARGADOR DE REGLAS
# ============================================================================

@dataclass
class ReglaNivel1:
    """Regla de categorización nivel 1 (basada en concepto)"""
    id: str
    patron: str
    tipo_match: str  # "exacto", "contiene", "comienza", "termina"
    categoria: str
    subcategoria: str
    prioridad: int
    activo: bool
    confianza_base: int
    notas: str = ""

    def match(self, concepto_normalizado: str) -> bool:
        """Verifica si el concepto coincide con el patrón"""
        if not self.activo:
            return False

        patron_norm = _norm(self.patron)

        if self.tipo_match == "exacto":
            return concepto_normalizado == patron_norm
        elif self.tipo_match == "contiene":
            return patron_norm in concepto_normalizado
        elif self.tipo_match == "comienza":
            return concepto_normalizado.startswith(patron_norm)
        elif self.tipo_match == "termina":
            return concepto_normalizado.endswith(patron_norm)
        else:
            return False


@dataclass
class PatronNivel2:
    """Patrón de refinamiento nivel 2 (basado en detalle)"""
    id: str
    palabras_clave: List[str]
    subcategoria_refinada: str
    confianza_refinada: int
    activo: bool
    notas: str = ""

    def match(self, detalle_normalizado: str) -> bool:
        """Verifica si el detalle contiene alguna palabra clave"""
        if not self.activo:
            return False

        for palabra in self.palabras_clave:
            palabra_norm = _norm(palabra)
            if palabra_norm in detalle_normalizado:
                return True
        return False


class CargadorReglas:
    """Carga y gestiona las reglas desde JSON"""

    def __init__(self, archivo_reglas: str = None):
        """
        Args:
            archivo_reglas: Path al archivo JSON. Si es None, usa el default.
        """
        if archivo_reglas is None:
            # Path relativo desde este archivo
            base_path = Path(__file__).parent.parent / "data"
            archivo_reglas = str(base_path / "reglas_cascada.json")

        self.archivo_reglas = archivo_reglas
        self.reglas_nivel1: List[ReglaNivel1] = []
        self.reglas_nivel2: Dict[str, List[PatronNivel2]] = {}
        self.categorias_disponibles: Dict[str, List[str]] = {}
        self._cargar_reglas()

    def _cargar_reglas(self):
        """Carga las reglas desde el archivo JSON"""
        try:
            with open(self.archivo_reglas, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Archivo de reglas no encontrado: {self.archivo_reglas}\n"
                f"Asegúrate de haber migrado las reglas del CLI."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parseando JSON de reglas: {e}")

        # Cargar reglas nivel 1
        for regla_data in data.get("nivel1_concepto", {}).get("reglas", []):
            regla = ReglaNivel1(
                id=regla_data["id"],
                patron=regla_data["patron"],
                tipo_match=regla_data["tipo_match"],
                categoria=regla_data["categoria"],
                subcategoria=regla_data["subcategoria"],
                prioridad=regla_data["prioridad"],
                activo=regla_data.get("activo", True),
                confianza_base=regla_data.get("confianza_base", 80),
                notas=regla_data.get("notas", "")
            )
            self.reglas_nivel1.append(regla)

        # Ordenar por prioridad (1 es mayor prioridad)
        self.reglas_nivel1.sort(key=lambda r: r.prioridad)

        # Cargar reglas nivel 2
        reglas_ref = data.get("nivel2_refinamiento", {}).get("reglas", {})
        for subcategoria_base, config in reglas_ref.items():
            patrones = []
            for patron_data in config.get("patrones", []):
                patron = PatronNivel2(
                    id=patron_data["id"],
                    palabras_clave=patron_data["palabras_clave"],
                    subcategoria_refinada=patron_data["subcategoria_refinada"],
                    confianza_refinada=patron_data.get("confianza_refinada", 85),
                    activo=patron_data.get("activo", True),
                    notas=patron_data.get("notas", "")
                )
                patrones.append(patron)

            self.reglas_nivel2[subcategoria_base] = patrones

        # Cargar categorías disponibles
        self.categorias_disponibles = data.get("categorias_disponibles", {})

    def get_reglas_nivel1(self) -> List[ReglaNivel1]:
        """Retorna todas las reglas de nivel 1 ordenadas por prioridad"""
        return self.reglas_nivel1

    def get_patrones_nivel2(self, subcategoria_base: str) -> List[PatronNivel2]:
        """Retorna los patrones de nivel 2 para una subcategoría base"""
        return self.reglas_nivel2.get(subcategoria_base, [])

    def get_subcategorias(self, categoria: str) -> List[str]:
        """Retorna las subcategorías disponibles para una categoría"""
        return self.categorias_disponibles.get(categoria, [])


# ============================================================================
# MOTOR DE CATEGORIZACIÓN
# ============================================================================

@dataclass
class ResultadoCategorizacion:
    """Resultado de la categorización de un movimiento"""
    categoria: str
    subcategoria: str
    confianza: int
    regla_nivel1_id: Optional[str] = None
    regla_nivel2_id: Optional[str] = None
    fue_refinado: bool = False


class CategorizadorCascada:
    """Motor de categorización en cascada de 2 niveles"""

    def __init__(self, archivo_reglas: str = None):
        """
        Args:
            archivo_reglas: Path al archivo JSON de reglas
        """
        self.cargador = CargadorReglas(archivo_reglas)

    def categorizar_nivel1(self, concepto: str) -> Tuple[str, str, int, Optional[str]]:
        """
        Categorización nivel 1 basada en el concepto del movimiento.

        Args:
            concepto: Campo concepto del movimiento bancario

        Returns:
            Tupla (categoria, subcategoria, confianza, regla_id)
        """
        concepto_norm = _norm(concepto)

        # Buscar primera regla que coincida (ya están ordenadas por prioridad)
        for regla in self.cargador.get_reglas_nivel1():
            if regla.match(concepto_norm):
                return (
                    regla.categoria,
                    regla.subcategoria,
                    regla.confianza_base,
                    regla.id
                )

        # Sin match: categoría desconocida
        return ("OTROS", "Sin_Clasificar", 0, None)

    def refinar_nivel2(
        self,
        detalle: str,
        subcategoria_base: str
    ) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Refinamiento nivel 2 basado en el detalle del movimiento.

        Args:
            detalle: Campo detalle del movimiento bancario
            subcategoria_base: Subcategoría obtenida en nivel 1

        Returns:
            Tupla (subcategoria_refinada, confianza, regla_id) o (None, 0, None) si no aplica
        """
        detalle_norm = _norm(detalle)

        # Obtener patrones de refinamiento para esta subcategoría
        patrones = self.cargador.get_patrones_nivel2(subcategoria_base)

        if not patrones:
            # No hay refinamiento disponible para esta subcategoría
            return (None, 0, None)

        # Buscar primer patrón que coincida
        for patron in patrones:
            if patron.match(detalle_norm):
                return (
                    patron.subcategoria_refinada,
                    patron.confianza_refinada,
                    patron.id
                )

        # Sin match en nivel 2: mantener subcategoría base
        return (None, 0, None)

    def categorizar_cascada(
        self,
        concepto: str,
        detalle: str,
        monto: float = 0.0
    ) -> ResultadoCategorizacion:
        """
        Categorización completa en cascada (nivel 1 → nivel 2).

        Incluye reglas fuertes pre-cascada para IVA y Débitos/Créditos.

        Args:
            concepto: Campo concepto del movimiento
            detalle: Campo detalle del movimiento
            monto: Monto del movimiento (opcional, para reglas futuras)

        Returns:
            ResultadoCategorizacion con categoría, subcategoría y confianza
        """
        # REGLAS FUERTES PRE-CASCADA (PRIORIDAD MÁXIMA)
        # Normalizar texto completo para reglas fuertes
        texto_completo = f"{concepto or ''} {detalle or ''}"
        texto_norm = normalize_text(texto_completo)

        # REGLA FUERTE A) Impuesto Débitos y Créditos (DB/CR)
        # Condiciones posibles:
        # - "DEBITOS" + "CREDITOS"
        # - "DEB" + "CRED"
        # - "DEBITOS Y CREDITOS"
        # - "DB" + "CR"
        if (
            ("DEBITOS" in texto_norm and "CREDITOS" in texto_norm) or
            ("DEB" in texto_norm and "CRED" in texto_norm) or
            ("DEBITOS Y CREDITOS" in texto_norm) or
            (" DB " in f" {texto_norm} " and " CR " in f" {texto_norm} ")
        ):
            return ResultadoCategorizacion(
                categoria="IMPUESTOS",
                subcategoria="Impuestos - Débitos y Créditos",
                confianza=90,
                regla_nivel1_id="REGLA_FUERTE_DBCR",
                regla_nivel2_id=None,
                fue_refinado=False
            )

        # REGLA FUERTE B) IVA
        # Usar espacios para evitar falsos positivos (ej: "VIVA" no debe matchear)
        if " IVA " in f" {texto_norm} ":
            return ResultadoCategorizacion(
                categoria="IMPUESTOS",
                subcategoria="Impuestos - IVA",
                confianza=90,
                regla_nivel1_id="REGLA_FUERTE_IVA",
                regla_nivel2_id=None,
                fue_refinado=False
            )

        # Si no matcheó reglas fuertes, continuar con cascada normal
        # Nivel 1: Categorización base
        categoria, subcategoria_base, confianza_base, regla_id1 = self.categorizar_nivel1(concepto)

        # Nivel 2: Intentar refinamiento
        subcategoria_refinada, confianza_ref, regla_id2 = self.refinar_nivel2(
            detalle,
            subcategoria_base
        )

        # Determinar resultado final
        if subcategoria_refinada:
            # Fue refinado en nivel 2
            return ResultadoCategorizacion(
                categoria=categoria,
                subcategoria=subcategoria_refinada,
                confianza=confianza_ref,
                regla_nivel1_id=regla_id1,
                regla_nivel2_id=regla_id2,
                fue_refinado=True
            )
        else:
            # Se mantiene la categorización de nivel 1
            return ResultadoCategorizacion(
                categoria=categoria,
                subcategoria=subcategoria_base,
                confianza=confianza_base,
                regla_nivel1_id=regla_id1,
                regla_nivel2_id=None,
                fue_refinado=False
            )


# ============================================================================
# FUNCIÓN PÚBLICA PARA INTEGRACIÓN CON API
# ============================================================================

def categorizar_movimientos(
    db: Session,
    solo_sin_categoria: bool = True,
    archivo_reglas: str = None
) -> Dict[str, Any]:
    """
    Categoriza movimientos en la base de datos usando el motor en cascada.

    ETAPA 4: Aplica reglas aprendidas ANTES de las reglas estáticas.

    Args:
        db: Sesión de SQLAlchemy
        solo_sin_categoria: Si True, solo procesa movimientos sin categoría
        archivo_reglas: Path al archivo de reglas (opcional)

    Returns:
        Diccionario con estadísticas de categorización
    """
    # ETAPA 4: Importar funciones de reglas aprendidas
    from backend.core.reglas_aprendidas import buscar_regla_aplicable, aplicar_regla_a_movimiento

    # Inicializar motor
    motor = CategorizadorCascada(archivo_reglas)

    # Query de movimientos
    q = db.query(Movimiento)
    if solo_sin_categoria:
        q = q.filter(
            or_(
                Movimiento.categoria == None,
                Movimiento.categoria == "SIN_CATEGORIA",
                Movimiento.categoria == ""
            )
        )

    movimientos = q.all()

    # Estadísticas
    procesados = 0
    categorizados = 0
    refinados = 0
    sin_match = 0
    aplicados_regla_aprendida = 0  # ETAPA 4: contador de reglas aprendidas
    por_categoria: Dict[str, int] = {}
    por_subcategoria: Dict[str, int] = {}

    # Procesar cada movimiento
    for mov in movimientos:
        procesados += 1

        # SKIP si el movimiento ya fue categorizado manualmente
        if hasattr(mov, 'confianza_fuente') and mov.confianza_fuente == "manual":
            # No pisar categorizaciones manuales
            continue

        # ETAPA 4: PASO 1 - Intentar aplicar regla aprendida primero
        regla_aplicable = buscar_regla_aplicable(mov.descripcion or "", db)

        if regla_aplicable:
            # Aplicar regla aprendida
            aplicar_regla_a_movimiento(regla_aplicable, mov, db)
            categorizados += 1
            aplicados_regla_aprendida += 1

            # Setear confianza_fuente (si no lo hizo aplicar_regla_a_movimiento)
            if hasattr(mov, 'confianza_fuente') and not mov.confianza_fuente:
                mov.confianza_fuente = "regla_aprendida"

            # Contadores
            key_cat = mov.categoria
            key_sub = f"{mov.categoria}:{mov.subcategoria}"
            por_categoria[key_cat] = por_categoria.get(key_cat, 0) + 1
            por_subcategoria[key_sub] = por_subcategoria.get(key_sub, 0) + 1

            # NO pasar por motor cascada si matcheó regla aprendida
            continue

        # ETAPA 4: PASO 2 - Si no matcheó regla aprendida, usar motor cascada (comportamiento actual)
        resultado = motor.categorizar_cascada(
            concepto=mov.descripcion or "",
            detalle=mov.descripcion or "",  # TODO: usar campo detalle cuando exista
            monto=mov.monto
        )

        # Actualizar movimiento
        mov.categoria = resultado.categoria
        mov.subcategoria = resultado.subcategoria
        mov.confianza_porcentaje = resultado.confianza

        # Setear confianza_fuente para cascada
        if hasattr(mov, 'confianza_fuente'):
            mov.confianza_fuente = "cascada"

        # Estadísticas
        if resultado.categoria != "OTROS":
            categorizados += 1
        else:
            sin_match += 1

        if resultado.fue_refinado:
            refinados += 1

        # Contadores
        key_cat = resultado.categoria
        key_sub = f"{resultado.categoria}:{resultado.subcategoria}"

        por_categoria[key_cat] = por_categoria.get(key_cat, 0) + 1
        por_subcategoria[key_sub] = por_subcategoria.get(key_sub, 0) + 1

    # Commit changes
    db.commit()

    # Preparar resultado
    categorias_distintas = sorted(por_categoria.keys())
    top_categorias = sorted(
        por_categoria.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    top_subcategorias = sorted(
        por_subcategoria.items(),
        key=lambda x: x[1],
        reverse=True
    )[:15]

    return {
        "procesados": procesados,
        "categorizados": categorizados,
        "sin_match": sin_match,
        "refinados_nivel2": refinados,
        "aplicados_regla_aprendida": aplicados_regla_aprendida,  # ETAPA 4
        "categorias_distintas": categorias_distintas,
        "top_categorias": top_categorias,
        "top_subcategorias": top_subcategorias,
        "porcentaje_categorizados": round((categorizados / procesados * 100), 2) if procesados > 0 else 0,
        "porcentaje_refinados": round((refinados / procesados * 100), 2) if procesados > 0 else 0,
        "motor": "CategorizadorCascada v2.0 + Reglas Aprendibles (ETAPA 4)"
    }


# ============================================================================
# FUNCIÓN DE UTILIDAD PARA TESTS
# ============================================================================

def categorizar_texto(concepto: str, detalle: str = "") -> ResultadoCategorizacion:
    """
    Función helper para categorizar un texto sin acceso a DB.
    Útil para tests y debugging.

    Args:
        concepto: Texto del concepto
        detalle: Texto del detalle (opcional)

    Returns:
        ResultadoCategorizacion
    """
    motor = CategorizadorCascada()
    return motor.categorizar_cascada(concepto, detalle)
