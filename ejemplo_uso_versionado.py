"""
Ejemplo práctico de uso del sistema de versionado de catálogo

Este script muestra cómo usar el sistema para hacer un upgrade
real de categorías en el proyecto TORO.
"""

import requests
import json

# Base URL del servidor TORO
BASE_URL = "http://localhost:8000"

def ejemplo_completo():
    """
    Ejemplo completo: Reorganizar categorías EGRESOS

    Escenario: Queremos reorganizar las subcategorías de EGRESOS
    para que sean más consistentes y fáciles de analizar.
    """

    print("=" * 70)
    print("EJEMPLO: Reorganización de Categorías EGRESOS v1.0.0 -> v2.0.0")
    print("=" * 70)

    # ========================================
    # PASO 1: Crear versión 2.0.0
    # ========================================
    print("\n[1/5] Creando versión 2.0.0...")

    response = requests.post(
        f"{BASE_URL}/api/admin/catalogo/version",
        json={
            "version": "2.0.0",
            "descripcion": "Reorganización EGRESOS: mejor estructura para análisis",
            "created_by": "admin"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Versión creada: {data['version']}")
        print(f"  ID: {data['version_id']}")
    else:
        print(f"✗ Error: {response.text}")
        return

    # ========================================
    # PASO 2: Definir mapeos de upgrade
    # ========================================
    print("\n[2/5] Definiendo mapeos de upgrade...")

    mapeos = {
        "mapeos": [
            # Consolidar prestadores médicos
            {
                "from_version": "1.0.0",
                "to_version": "2.0.0",
                "from_cat": "EGRESOS",
                "from_sub": "Prestadores_Farmacias",
                "to_cat": "EGRESOS",
                "to_sub": "Salud - Prestadores",
                "action": "RENAME"
            },
            {
                "from_version": "1.0.0",
                "to_version": "2.0.0",
                "from_cat": "EGRESOS",
                "from_sub": "Medicos_Consultas",
                "to_cat": "EGRESOS",
                "to_sub": "Salud - Consultas Médicas",
                "action": "RENAME"
            },
            # Reorganizar servicios
            {
                "from_version": "1.0.0",
                "to_version": "2.0.0",
                "from_cat": "EGRESOS",
                "from_sub": "Servicios_Internet",
                "to_cat": "EGRESOS",
                "to_sub": "Servicios - Internet y Telefonía",
                "action": "RENAME"
            },
            # Mover educación a inversiones
            {
                "from_version": "1.0.0",
                "to_version": "2.0.0",
                "from_cat": "EGRESOS",
                "from_sub": "Educacion_Cursos",
                "to_cat": "INVERSIONES",
                "to_sub": "Desarrollo Personal",
                "action": "MOVE"
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/api/admin/catalogo/upgrade-map",
        json=mapeos
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Mapeos cargados: {data['mapeos_creados']}")
    else:
        print(f"✗ Error: {response.text}")
        return

    # ========================================
    # PASO 3: Simular impacto
    # ========================================
    print("\n[3/5] Simulando impacto del upgrade...")

    response = requests.post(
        f"{BASE_URL}/api/admin/catalogo/upgrade/simular",
        json={
            "from_version": "1.0.0",
            "to_version": "2.0.0"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Simulación completada")
        print(f"  Total movimientos afectados: {data['total_afectados']}")

        if data['top_mapeos']:
            print(f"\n  Top mapeos:")
            for mapeo in data['top_mapeos'][:5]:
                print(f"    • {mapeo['from_cat']}/{mapeo['from_sub']}")
                print(f"      -> {mapeo['to_cat']}/{mapeo['to_sub']}")
                print(f"      Afectados: {mapeo['affected_count']} | Acción: {mapeo['action']}")
        else:
            print("  ⚠ No hay movimientos que coincidan con los mapeos")
    else:
        print(f"✗ Error: {response.text}")
        return

    # ========================================
    # PASO 4: Confirmar con usuario
    # ========================================
    print("\n[4/5] Confirmación del usuario")
    print("¿Desea aplicar el upgrade? (s/n): ", end="")
    confirmacion = input().strip().lower()

    if confirmacion != 's':
        print("✗ Operación cancelada por el usuario")
        return

    # ========================================
    # PASO 5: Aplicar upgrade
    # ========================================
    print("\n[5/5] Aplicando upgrade...")

    # Aplicar solo a batch 1 como prueba
    response = requests.post(
        f"{BASE_URL}/api/admin/catalogo/upgrade/aplicar",
        json={
            "from_version": "1.0.0",
            "to_version": "2.0.0",
            "confirm": True,
            "actor": "admin",
            "scope": {
                "batch_id": 1  # Solo batch 1 como prueba
            }
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Upgrade aplicado exitosamente")
        print(f"  Procesados: {data['total_procesados']}")
        print(f"  Actualizados: {data['total_actualizados']}")
        print(f"  Preservados (manual): {data['total_preservados']}")
        print(f"  Audit ID: {data['audit_id']}")
    else:
        print(f"✗ Error: {response.text}")
        return

    print("\n" + "=" * 70)
    print("✓ PROCESO COMPLETADO")
    print("=" * 70)


def ejemplo_rollback():
    """
    Ejemplo: Cómo revertir un upgrade (rollback)

    Nota: Para hacer rollback, crear mapeos inversos y aplicar.
    """
    print("\n" + "=" * 70)
    print("EJEMPLO: Rollback de v2.0.0 -> v1.0.0")
    print("=" * 70)

    print("\nPara hacer rollback:")
    print("1. Crear mapeos inversos (2.0.0 -> 1.0.0)")
    print("2. Aplicar upgrade con esos mapeos")
    print("\nEjemplo de mapeo inverso:")
    print(json.dumps({
        "from_version": "2.0.0",
        "to_version": "1.0.0",
        "from_cat": "EGRESOS",
        "from_sub": "Salud - Prestadores",
        "to_cat": "EGRESOS",
        "to_sub": "Prestadores_Farmacias",
        "action": "RENAME"
    }, indent=2))


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  SISTEMA DE VERSIONADO DE CATÁLOGO - EJEMPLOS DE USO          ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("\nNOTA: Asegúrate de que el servidor TORO esté ejecutándose")
    print("      (python run.py o python run_dev.py)")

    print("\n[1] Ejemplo completo de upgrade")
    print("[2] Ejemplo de rollback")
    print("[0] Salir")

    opcion = input("\nSelecciona una opción: ").strip()

    if opcion == "1":
        ejemplo_completo()
    elif opcion == "2":
        ejemplo_rollback()
    else:
        print("Saliendo...")
