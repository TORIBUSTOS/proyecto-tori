"""
Utilidades para Reglas Aprendibles (ETAPA 4).

Funciones de normalización y generación de patrones para
el sistema de aprendizaje de categorización.
"""
import re
from typing import List
from sqlalchemy.orm import Session
from backend.models.regla_categorizacion import ReglaCategorizacion


def normalizar_texto(texto: str) -> str:
    """
    Normaliza un texto para generar patrones consistentes.

    Args:
        texto: Texto a normalizar

    Returns:
        Texto normalizado (uppercase, sin espacios múltiples, sin caracteres especiales)

    Ejemplo:
        >>> normalizar_texto("  Compra   VISA!!!  ")
        "COMPRA VISA"
    """
    if not texto:
        return ""

    # Convertir a mayúsculas
    texto = texto.upper()

    # Strip inicial
    texto = texto.strip()

    # Remover caracteres especiales, dejando solo letras, números y espacios
    texto = re.sub(r'[^A-Z0-9\s]', '', texto)

    # Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)

    # Strip final
    texto = texto.strip()

    return texto


def generar_patron_desde_descripcion(descripcion: str, max_palabras: int = 5) -> str:
    """
    Genera un patrón normalizado desde una descripción de movimiento.

    Toma las primeras N palabras de la descripción normalizada para crear
    un patrón que pueda matchear movimientos similares.

    Args:
        descripcion: Descripción del movimiento
        max_palabras: Número máximo de palabras a incluir en el patrón (default: 5)

    Returns:
        Patrón normalizado

    Ejemplo:
        >>> generar_patron_desde_descripcion("COMPRA VISA DEBITO COMERCIO PEDIDOSYA ENTREGA 123")
        "COMPRA VISA DEBITO COMERCIO PEDIDOSYA"
    """
    texto_normalizado = normalizar_texto(descripcion)

    if not texto_normalizado:
        return ""

    # Tomar las primeras N palabras
    palabras = texto_normalizado.split()[:max_palabras]

    # Unir con espacio
    patron = ' '.join(palabras)

    return patron


def buscar_regla_aplicable(descripcion: str, db: Session) -> ReglaCategorizacion | None:
    """
    Busca una regla aprendida que sea aplicable a la descripción dada.

    Busca reglas cuyo patrón esté contenido en la descripción normalizada,
    ordenadas por confianza y uso.

    Args:
        descripcion: Descripción del movimiento
        db: Sesión de base de datos

    Returns:
        Primera regla aplicable encontrada, o None si no hay match
    """
    descripcion_normalizada = normalizar_texto(descripcion)

    if not descripcion_normalizada:
        return None

    # Obtener todas las reglas ordenadas por confianza y uso
    reglas = db.query(ReglaCategorizacion)\
        .order_by(ReglaCategorizacion.confianza.desc(), ReglaCategorizacion.veces_usada.desc())\
        .all()

    # Buscar primera regla cuyo patrón esté contenido en la descripción
    for regla in reglas:
        if regla.patron in descripcion_normalizada:
            return regla

    return None


def aplicar_regla_a_movimiento(regla: ReglaCategorizacion, movimiento, db: Session) -> bool:
    """
    Aplica una regla aprendida a un movimiento.

    Actualiza la categoría y subcategoría del movimiento según la regla,
    incrementa contadores de uso y confianza de la regla.

    Args:
        regla: Regla a aplicar
        movimiento: Movimiento a categorizar
        db: Sesión de base de datos

    Returns:
        True si se aplicó la regla exitosamente
    """
    # Setear categoría y subcategoría
    movimiento.categoria = regla.categoria
    movimiento.subcategoria = regla.subcategoria

    # Actualizar confianza del movimiento (usar la mayor)
    if movimiento.confianza_porcentaje is None:
        movimiento.confianza_porcentaje = regla.confianza
    else:
        movimiento.confianza_porcentaje = max(movimiento.confianza_porcentaje, regla.confianza)

    # Incrementar uso de la regla
    regla.veces_usada += 1

    # Incrementar confianza de la regla (máximo 100)
    regla.confianza = min(100, regla.confianza + 1)

    return True


def obtener_o_crear_regla(
    patron: str,
    categoria: str,
    subcategoria: str,
    db: Session
) -> ReglaCategorizacion:
    """
    Obtiene una regla existente o crea una nueva.

    Si existe una regla con el mismo patrón:
    - Incrementa veces_usada
    - Incrementa confianza (máximo 100)
    - Actualiza categoría/subcategoría (la última corrección manda)

    Si no existe:
    - Crea nueva regla con confianza=50, veces_usada=1

    Args:
        patron: Patrón normalizado
        categoria: Categoría a asignar
        subcategoria: Subcategoría a asignar
        db: Sesión de base de datos

    Returns:
        Regla obtenida o creada
    """
    # Buscar regla existente
    regla = db.query(ReglaCategorizacion).filter(ReglaCategorizacion.patron == patron).first()

    if regla:
        # Regla existente: actualizar
        regla.veces_usada += 1
        regla.confianza = min(100, regla.confianza + 10)
        regla.categoria = categoria
        regla.subcategoria = subcategoria
    else:
        # Nueva regla: crear
        regla = ReglaCategorizacion(
            patron=patron,
            categoria=categoria,
            subcategoria=subcategoria,
            confianza=50,
            veces_usada=1
        )
        db.add(regla)

    db.commit()
    db.refresh(regla)

    return regla
