"""
Extractores de metadata de movimientos bancarios.

Este módulo contiene funciones puras (sin efectos secundarios) para extraer
información estructurada de las descripciones de movimientos bancarios.

Principios:
- Funciones puras: sin DB, sin estado, sin side effects
- Retornan None si no encuentran lo que buscan (no excepciones)
- Case-insensitive donde corresponda
- Tolerantes a variaciones de formato
"""

import re
from typing import Optional


def extraer_nombre(detalle: str) -> Optional[str]:
    """
    Extrae el nombre de una persona/entidad de la descripción del movimiento.

    Patrones soportados:
    - "NOMBRE: APELLIDO NOMBRE" (transferencias)
    - "NOMBRE: RAZON SOCIAL" (transferencias empresas)
    - "TERMINAL: XXX NOMBRE: YYY" (más contexto)

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        Nombre extraído (sin el prefijo "NOMBRE:") o None si no encuentra

    Examples:
        >>> extraer_nombre("Crédito por Transferencia - NOMBRE: DORADO GABRIELA BEATRIZ DOCUMENTO: 12345678")
        "DORADO GABRIELA BEATRIZ"

        >>> extraer_nombre("NOMBRE: SANARTE SRL DOCUMENTO: 30712384960")
        "SANARTE SRL"

        >>> extraer_nombre("Compra sin nombre")
        None
    """
    if not detalle:
        return None

    # Patrón: NOMBRE: seguido de texto en mayúsculas hasta DOCUMENTO o final
    # Captura todo después de "NOMBRE:" hasta "DOCUMENTO:" o fin de línea
    patron = r'NOMBRE:\s*([A-ZÁÉÍÓÚÑ\s/,\.\-]+?)(?:\s+DOCUMENTO:|$)'

    match = re.search(patron, detalle, re.IGNORECASE)
    if match:
        nombre = match.group(1).strip()
        # Limpiar espacios múltiples
        nombre = re.sub(r'\s+', ' ', nombre)
        return nombre if nombre else None

    return None


def extraer_documento(detalle: str) -> Optional[str]:
    """
    Extrae el número de documento (CUIT/CUIL/DNI) de la descripción.

    Patrones soportados:
    - "DOCUMENTO: 12345678" (DNI 8 dígitos)
    - "DOCUMENTO: 20123456789" (CUIL/CUIT 11 dígitos)
    - "ID:30712384960" (CUIT en débitos automáticos)

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        Número de documento como string o None si no encuentra

    Examples:
        >>> extraer_documento("NOMBRE: JUAN PEREZ DOCUMENTO: 12345678")
        "12345678"

        >>> extraer_documento("ID:30712384960 PRES:AFIP")
        "30712384960"

        >>> extraer_documento("Sin documento")
        None
    """
    if not detalle:
        return None

    # Patrón 1: DOCUMENTO: seguido de 8-11 dígitos
    patron_doc = r'DOCUMENTO:\s*(\d{8,11})'
    match = re.search(patron_doc, detalle, re.IGNORECASE)
    if match:
        return match.group(1)

    # Patrón 2: ID: seguido de 8-11 dígitos (débitos automáticos)
    patron_id = r'ID:(\d{8,11})'
    match = re.search(patron_id, detalle, re.IGNORECASE)
    if match:
        doc = match.group(1)
        # Validar que sea CUIT/CUIL (11 dígitos) o DNI (8 dígitos)
        if len(doc) in [8, 11]:
            return doc

    return None


def es_debin(concepto: str, detalle: str) -> bool:
    """
    Detecta si un movimiento es un DEBIN (Débito Inmediato).

    Busca la palabra clave "DEBIN" en concepto o detalle.

    Args:
        concepto: Campo concepto del movimiento
        detalle: Descripción completa del movimiento

    Returns:
        True si es DEBIN, False caso contrario

    Examples:
        >>> es_debin("Debito DEBIN", "CONCEPTO_QB: 8 LEYENDA: Transferencia enviada")
        True

        >>> es_debin("Credito DEBIN", "LEYENDA: Transferencia recibida")
        True

        >>> es_debin("Transferencia", "Por CBU")
        False
    """
    if not concepto and not detalle:
        return False

    texto_completo = f"{concepto or ''} {detalle or ''}".upper()
    return 'DEBIN' in texto_completo


def extraer_debin_id(detalle: str) -> Optional[str]:
    """
    Extrae el ID único del DEBIN de la descripción.

    Patrones soportados:
    - "ID_DEBIN: 2512010000125350751512" (numérico largo)
    - "ID_DEBIN: L18M" (alfanumérico corto)
    - "ID_DEBIN: WY7Z" (código corto)

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        ID del DEBIN o None si no encuentra

    Examples:
        >>> extraer_debin_id("ID_DEBIN: 2512010000125350751512 DOCUMENTO: 123")
        "2512010000125350751512"

        >>> extraer_debin_id("ID_DEBIN: L18M NOMBRE: SANARTE")
        "L18M"

        >>> extraer_debin_id("Sin debin")
        None
    """
    if not detalle:
        return None

    # Patrón: ID_DEBIN: seguido de alfanumérico (4-25 caracteres)
    patron = r'ID_DEBIN:\s*([A-Z0-9]{4,25})'

    match = re.search(patron, detalle, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extraer_cbu(detalle: str) -> Optional[str]:
    """
    Extrae el CBU (Clave Bancaria Uniforme) de transferencias.

    Patrón: "CBU: 22 dígitos"

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        CBU de 22 dígitos o None si no encuentra

    Examples:
        >>> extraer_cbu("CBU: 0070076430004136307784 DOCUMENTO: 123")
        "0070076430004136307784"

        >>> extraer_cbu("Sin CBU")
        None
    """
    if not detalle:
        return None

    # Patrón: CBU: seguido de exactamente 22 dígitos
    patron = r'CBU:\s*(\d{22})'

    match = re.search(patron, detalle, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extraer_terminal(detalle: str) -> Optional[str]:
    """
    Extrae el código de terminal bancaria de la descripción.

    Patrones: TERMINAL: XXXX0001, MBBM0001, LINK0012100C5, etc.

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        Código de terminal o None si no encuentra

    Examples:
        >>> extraer_terminal("TERMINAL: MBSP0001 NOMBRE: JUAN")
        "MBSP0001"

        >>> extraer_terminal("TERMINAL: LINK0012100C5")
        "LINK0012100C5"
    """
    if not detalle:
        return None

    # Patrón: TERMINAL: seguido de código alfanumérico (4-15 chars)
    patron = r'TERMINAL:\s*([A-Z0-9]{4,15})'

    match = re.search(patron, detalle, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extraer_comercio(detalle: str) -> Optional[str]:
    """
    Extrae el nombre del comercio en compras con tarjeta.

    Patrón: "COMERCIO: NOMBRE_COMERCIO OPERACION:"

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        Nombre del comercio o None si no encuentra

    Examples:
        >>> extraer_comercio("COMERCIO: PEDIDOSYA PROPINAS OPERACION: 982948")
        "PEDIDOSYA PROPINAS"

        >>> extraer_comercio("COMERCIO: OPENAI *CHATGPT SUBSCR OPERACION: 779574")
        "OPENAI *CHATGPT SUBSCR"
    """
    if not detalle:
        return None

    # Patrón: COMERCIO: seguido de texto hasta OPERACION:
    patron = r'COMERCIO:\s*([A-Z0-9\s\*\-\./]+?)(?:\s+OPERACION:|$)'

    match = re.search(patron, detalle, re.IGNORECASE)
    if match:
        comercio = match.group(1).strip()
        # Limpiar espacios múltiples
        comercio = re.sub(r'\s+', ' ', comercio)
        return comercio if comercio else None

    return None


def extraer_referencia(detalle: str) -> Optional[str]:
    """
    Extrae la referencia de débitos automáticos de servicios.

    Patrón: "REF:XXXXXX"

    Args:
        detalle: Descripción completa del movimiento

    Returns:
        Referencia del servicio o None si no encuentra

    Examples:
        >>> extraer_referencia("PRES:SERV AGUA REF:01569339387")
        "01569339387"

        >>> extraer_referencia("REF:FC2811-67404620")
        "FC2811-67404620"
    """
    if not detalle:
        return None

    # Patrón: REF: seguido de alfanumérico/guiones (hasta 30 chars)
    patron = r'REF:([A-Z0-9\-]{3,30})'

    match = re.search(patron, detalle, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


# ============================================================================
# HELPER: Función de utilidad para extraer todo de un movimiento
# ============================================================================

def extraer_metadata_completa(concepto: str, detalle: str) -> dict:
    """
    Extrae toda la metadata disponible de un movimiento.

    Esta es una función de conveniencia que ejecuta todos los extractores
    y retorna un diccionario con todos los campos encontrados.

    Args:
        concepto: Campo concepto del movimiento
        detalle: Descripción completa del movimiento

    Returns:
        Diccionario con todos los campos de metadata (None si no encuentra)

    Example:
        >>> extraer_metadata_completa(
        ...     "Credito DEBIN",
        ...     "LEYENDA: Transferencia recibida NOMBRE: SANARTE SRL DOCUMENTO: 30712384960 ID_DEBIN: L18M"
        ... )
        {
            'persona_nombre': 'SANARTE SRL',
            'documento': '30712384960',
            'es_debin': True,
            'debin_id': 'L18M',
            'cbu': None,
            'terminal': None,
            'comercio': None,
            'referencia': None
        }
    """
    return {
        'persona_nombre': extraer_nombre(detalle),
        'documento': extraer_documento(detalle),
        'es_debin': es_debin(concepto, detalle),
        'debin_id': extraer_debin_id(detalle) if es_debin(concepto, detalle) else None,
        'cbu': extraer_cbu(detalle),
        'terminal': extraer_terminal(detalle),
        'comercio': extraer_comercio(detalle),
        'referencia': extraer_referencia(detalle)
    }
