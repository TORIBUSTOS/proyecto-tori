"""
Test del sistema de versionado y upgrade de catálogo

Prueba el flujo completo:
1. Crear versión
2. Cargar mapeos
3. Simular upgrade
4. Aplicar upgrade
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import SessionLocal
from backend.models import CatalogVersion, CatalogUpgradeMap, Movimiento, AuditLog
from backend.core.catalog_upgrade import simular_upgrade, aplicar_upgrade
from datetime import datetime


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_1_crear_versiones():
    """Test: Crear versiones de catálogo"""
    print_header("TEST 1: Crear versiones")

    db = SessionLocal()

    # Crear versión baseline
    v1 = CatalogVersion(
        version="1.0.0",
        descripcion="Versión baseline original",
        created_by="system"
    )
    db.add(v1)

    # Crear versión 2.0.0
    v2 = CatalogVersion(
        version="2.0.0",
        descripcion="Reorganización de categorías EGRESOS",
        created_by="admin"
    )
    db.add(v2)

    db.commit()

    # Listar versiones
    versiones = db.query(CatalogVersion).all()
    print(f"\n✓ Versiones creadas: {len(versiones)}")
    for v in versiones:
        print(f"  - {v.version}: {v.descripcion}")

    db.close()


def test_2_cargar_mapeos():
    """Test: Cargar mapeos de upgrade"""
    print_header("TEST 2: Cargar mapeos de upgrade")

    db = SessionLocal()

    # Ejemplo: Reorganización de categorías EGRESOS
    mapeos = [
        # RENAME: Cambiar "Prestadores_Farmacias" a "Salud - Prestadores"
        CatalogUpgradeMap(
            from_version="1.0.0",
            to_version="2.0.0",
            from_cat="EGRESOS",
            from_sub="Prestadores_Farmacias",
            to_cat="EGRESOS",
            to_sub="Salud - Prestadores",
            action="RENAME"
        ),
        # MOVE: Mover "Educacion_Cursos" a otra categoría
        CatalogUpgradeMap(
            from_version="1.0.0",
            to_version="2.0.0",
            from_cat="EGRESOS",
            from_sub="Educacion_Cursos",
            to_cat="INVERSIONES",
            to_sub="Desarrollo Personal",
            action="MOVE"
        ),
    ]

    for m in mapeos:
        db.add(m)

    db.commit()

    # Listar mapeos
    all_mapeos = db.query(CatalogUpgradeMap).all()
    print(f"\n✓ Mapeos cargados: {len(all_mapeos)}")
    for m in all_mapeos:
        print(f"  - {m.action}: {m.from_cat}/{m.from_sub} -> {m.to_cat}/{m.to_sub}")

    db.close()


def test_3_simular_upgrade():
    """Test: Simular impacto de upgrade"""
    print_header("TEST 3: Simular upgrade")

    db = SessionLocal()

    # Simular upgrade de 1.0.0 a 2.0.0
    resultado = simular_upgrade(
        db=db,
        from_version="1.0.0",
        to_version="2.0.0"
    )

    if "error" in resultado:
        print(f"\n✗ Error: {resultado['error']}")
    else:
        print(f"\n✓ Total afectados: {resultado['total_afectados']} movimientos")
        print(f"\nTop mapeos:")
        for m in resultado["top_mapeos"][:5]:  # Mostrar top 5
            print(f"  - {m['from_cat']}/{m['from_sub']} -> {m['to_cat']}/{m['to_sub']}")
            print(f"    Afectados: {m['affected_count']} | Acción: {m['action']}")

    db.close()


def test_4_aplicar_upgrade():
    """Test: Aplicar upgrade real"""
    print_header("TEST 4: Aplicar upgrade")

    db = SessionLocal()

    # Contar movimientos antes
    total_antes = db.query(Movimiento).count()
    print(f"\nMovimientos antes: {total_antes}")

    # Aplicar upgrade con scope limitado (solo un batch para test)
    resultado = aplicar_upgrade(
        db=db,
        from_version="1.0.0",
        to_version="2.0.0",
        confirm=True,
        actor="test_script",
        scope={"batch_id": 1}  # Solo batch 1 para test
    )

    if "error" in resultado:
        print(f"\n✗ Error: {resultado['error']}")
    else:
        print(f"\n✓ Upgrade aplicado:")
        print(f"  - Procesados: {resultado['total_procesados']}")
        print(f"  - Actualizados: {resultado['total_actualizados']}")
        print(f"  - Preservados (manual): {resultado['total_preservados']}")
        print(f"  - Audit ID: {resultado['audit_id']}")

    db.close()


def test_5_verificar_auditoria():
    """Test: Verificar registros de auditoría"""
    print_header("TEST 5: Verificar auditoría")

    db = SessionLocal()

    # Obtener últimos 5 registros de auditoría
    audits = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).limit(5).all()

    print(f"\n✓ Últimos {len(audits)} registros de auditoría:")
    for a in audits:
        print(f"\n  [{a.created_at.strftime('%Y-%m-%d %H:%M:%S')}]")
        print(f"  Actor: {a.actor}")
        print(f"  Acción: {a.action}")
        print(f"  Entidad: {a.entity}")
        if a.after:
            print(f"  After: {a.after}")

    db.close()


def run_all_tests():
    """Ejecuta todos los tests en secuencia"""
    print("\n" + "=" * 60)
    print("  SISTEMA DE VERSIONADO Y UPGRADE DE CATÁLOGO")
    print("  Test Suite Completo")
    print("=" * 60)

    try:
        test_1_crear_versiones()
        test_2_cargar_mapeos()
        test_3_simular_upgrade()
        test_4_aplicar_upgrade()
        test_5_verificar_auditoria()

        print("\n" + "=" * 60)
        print("  ✓ TODOS LOS TESTS COMPLETADOS")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Primero ejecutar migración para crear tablas
    print("\n[INFO] Ejecutando migración de tablas...")
    from backend.database.migrate_add_catalog_versioning import migrate
    migrate()

    # Luego ejecutar tests
    run_all_tests()
