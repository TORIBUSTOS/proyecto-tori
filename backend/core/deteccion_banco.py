"""
Módulo de detección automática de banco desde archivos Excel
Identifica el origen del extracto bancario sin procesarlo completamente
"""

import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Constantes de bancos soportados
BANK_SUPERVIELLE = "SUPERVIELLE"
BANK_GALICIA = "GALICIA"
BANK_DESCONOCIDO = "DESCONOCIDO"


def detectar_banco_desde_excel(file_bytes: bytes) -> str:
    """
    Detecta el banco de origen analizando las primeras filas del Excel.

    Estrategia:
    1. Lee solo la primera hoja y las primeras 30 filas (optimización)
    2. Busca keywords específicos de cada banco
    3. Retorna el banco detectado o DESCONOCIDO

    Args:
        file_bytes: Contenido del archivo Excel en bytes

    Returns:
        str: BANK_SUPERVIELLE, BANK_GALICIA o BANK_DESCONOCIDO
    """
    try:
        # Leer solo primeras 30 filas de la primera hoja
        df = pd.read_excel(
            BytesIO(file_bytes),
            sheet_name=0,
            nrows=30,
            header=None  # Sin header para buscar en todas las celdas
        )

        # Convertir todo el dataframe a string para búsqueda
        contenido_completo = df.astype(str).values.flatten()
        texto_busqueda = ' '.join(contenido_completo).upper()

        # Heurísticas de detección

        # 1. Detectar SUPERVIELLE
        keywords_supervielle = [
            "SUPERVIELLE",
            "BANCO SUPERVIELLE",
            "WWW.SUPERVIELLE.COM.AR"
        ]

        # Columnas típicas de Supervielle (del parser actual)
        columnas_supervielle = [
            "FECHA",
            "MOVIMIENTO",
            "REFERENCIA",
            "IMPORTE",
            "SALDO"
        ]

        supervielle_score = 0
        for keyword in keywords_supervielle:
            if keyword in texto_busqueda:
                supervielle_score += 2

        for col in columnas_supervielle:
            if col in texto_busqueda:
                supervielle_score += 1

        # 2. Detectar GALICIA
        keywords_galicia = [
            "BANCO GALICIA",
            "GALICIA",
            "WWW.GALICIA.COM.AR",
            "GRUPO DE CONCEPTOS",
            "DESCRIPCIÓN",
            "MOVIMIENTOS CUENTA"
        ]

        columnas_galicia = [
            "FECHA",
            "CONCEPTO",
            "DESCRIPCIÓN",
            "GRUPO DE CONCEPTOS",
            "DÉBITO",
            "CRÉDITO"
        ]

        galicia_score = 0
        for keyword in keywords_galicia:
            if keyword in texto_busqueda:
                galicia_score += 2

        for col in columnas_galicia:
            if col in texto_busqueda:
                galicia_score += 1

        # Decisión basada en scores
        if supervielle_score > 0 and supervielle_score > galicia_score:
            logger.info(f"✅ Banco detectado: SUPERVIELLE (score: {supervielle_score})")
            return BANK_SUPERVIELLE
        elif galicia_score > 0 and galicia_score > supervielle_score:
            logger.info(f"✅ Banco detectado: GALICIA (score: {galicia_score})")
            return BANK_GALICIA
        else:
            logger.warning(f"⚠️ Banco no detectado (Supervielle: {supervielle_score}, Galicia: {galicia_score})")
            return BANK_DESCONOCIDO

    except Exception as e:
        logger.error(f"❌ Error detectando banco: {e}")
        return BANK_DESCONOCIDO


def obtener_nombre_banco(codigo_banco: str) -> str:
    """
    Retorna el nombre legible del banco.

    Args:
        codigo_banco: Código del banco (SUPERVIELLE, GALICIA, etc.)

    Returns:
        str: Nombre legible del banco
    """
    nombres = {
        BANK_SUPERVIELLE: "Banco Supervielle",
        BANK_GALICIA: "Banco Galicia",
        BANK_DESCONOCIDO: "Banco Desconocido"
    }
    return nombres.get(codigo_banco, "Banco Desconocido")
