"""
Helper para leer el catálogo de categorías desde JSON (MVP read-only)

Este módulo proporciona acceso centralizado al catálogo de categorías y subcategorías,
permitiendo mostrar labels humanos en lugar de keys técnicas.
"""

import json
import os
from functools import lru_cache
from pathlib import Path


def _get_catalog_path():
    """Obtiene la ruta absoluta al archivo categorias.json"""
    # backend/core/categorias_catalogo.py -> backend/ -> backend/config/categorias.json
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent
    catalog_path = backend_dir / "config" / "categorias.json"
    return catalog_path


@lru_cache(maxsize=1)
def load_catalog():
    """
    Carga el catálogo completo desde JSON con cache LRU

    Returns:
        dict: Catálogo completo con version, updated_at, categorias
    """
    catalog_path = _get_catalog_path()

    if not catalog_path.exists():
        # Fallback: catálogo vacío
        return {
            "version": "1.0.0",
            "updated_at": None,
            "categorias": []
        }

    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_catalog(version: str | None = None) -> dict:
    """
    Obtiene el catálogo para una versión específica.

    NOTA: Por ahora, el versionado es lógico (metadata + mapeos).
    El JSON baseline es el mismo para todas las versiones.

    Args:
        version: Versión del catálogo (opcional). Si es None, usa baseline.

    Returns:
        dict: Catálogo con metadato de versión
    """
    catalog = load_catalog()

    # Si no se especifica versión, retornar baseline
    if version is None:
        return catalog

    # Agregar metadato de versión solicitada
    result = catalog.copy()
    result["requested_version"] = version

    return result


def get_tree():
    """
    Obtiene solo la lista de categorías (árbol jerárquico)

    Returns:
        list: Lista de categorías con subcategorías anidadas
    """
    catalog = load_catalog()
    return catalog.get("categorias", [])


def get_categoria_label(key: str) -> str:
    """
    Obtiene el label humano de una categoría por su key

    Args:
        key: Key de la categoría (ej: "IMPUESTOS")

    Returns:
        str: Label humano (ej: "Impuestos") o la key si no se encuentra
    """
    tree = get_tree()
    for cat in tree:
        if cat.get("key") == key:
            return cat.get("label", key)
    return key


def get_subcategoria_label(subcategoria_key: str) -> str:
    """
    Obtiene el label humano de una subcategoría por su key

    Args:
        subcategoria_key: Key de la subcategoría (ej: "Impuestos - IVA")

    Returns:
        str: Label humano (ej: "IVA") o la key si no se encuentra
    """
    tree = get_tree()
    for cat in tree:
        for sub in cat.get("subcategorias", []):
            if sub.get("key") == subcategoria_key:
                return sub.get("label", subcategoria_key)
    return subcategoria_key


def get_subcategorias_by_categoria(categoria_key: str) -> list:
    """
    Obtiene todas las subcategorías de una categoría específica

    Args:
        categoria_key: Key de la categoría (ej: "IMPUESTOS")

    Returns:
        list: Lista de subcategorías [{key, label}, ...]
    """
    tree = get_tree()
    for cat in tree:
        if cat.get("key") == categoria_key:
            return cat.get("subcategorias", [])
    return []


# Funciones de utilidad adicionales

def get_all_categoria_keys() -> list:
    """Obtiene todas las keys de categorías disponibles"""
    tree = get_tree()
    return [cat.get("key") for cat in tree if cat.get("key")]


def get_all_subcategoria_keys() -> list:
    """Obtiene todas las keys de subcategorías disponibles"""
    tree = get_tree()
    keys = []
    for cat in tree:
        for sub in cat.get("subcategorias", []):
            if sub.get("key"):
                keys.append(sub.get("key"))
    return keys
