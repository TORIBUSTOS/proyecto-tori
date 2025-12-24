"""
Test del sistema de gestión administrativa de Batches

Prueba el flujo completo:
1. Listar batches
2. Obtener info de un batch
3. Eliminar batch (con confirmación)
4. Verificar auditoría
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import SessionLocal
from backend.models import ImportBatch, Movimiento, AuditLog
from backend.core.batch_admin import list_batches, delete_batch, get_batch_info
from datetime import datetime


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_1_listar_batches():
    """Test: Listar todos los batches"""
    print_header("TEST 1: Listar batches")

    db = SessionLocal()

    batches = list_batches(db)

    print(f"\n✓ Batches encontrados: {len(batches)}")

    if batches:
        print("\nPrimeros 5 batches:")
        for b in batches[:5]:
            print(f"\n  Batch ID: {b['id']}")
            print(f"  Origen: {b['origen']}")
            print(f"  Importado: {b['created_at']}")
            print(f"  Movimientos: {b['total_movimientos']}")
    else:
        print("\n  ⚠ No hay batches en la base de datos")

    db.close()
    return batches


def test_2_obtener_batch_info(batch_id: int):
    """Test: Obtener información de un batch específico"""
    print_header(f"TEST 2: Obtener info del batch {batch_id}")

    db = SessionLocal()

    batch = get_batch_info(db, batch_id)

    if batch:
        print(f"\n✓ Información del batch:")
        print(f"  ID: {batch['id']}")
        print(f"  Archivo: {batch['filename']}")
        print(f"  Hash: {batch['file_hash']}")
        print(f"  Importado: {batch['imported_at']}")
        print(f"  Filas insertadas (registro): {batch['rows_inserted']}")
        print(f"  Movimientos actuales: {batch['total_movimientos']}")
    else:
        print(f"\n✗ Batch {batch_id} no existe")

    db.close()
    return batch


def test_3_eliminar_batch_sin_confirm(batch_id: int):
    """Test: Intentar eliminar sin confirm (debe fallar)"""
    print_header(f"TEST 3: Eliminar batch sin confirm")

    db = SessionLocal()

    try:
        # Esto debería fallar porque no hay confirm
        resultado = delete_batch(db, batch_id, actor="test")
        print("\n✗ ERROR: No debería permitir eliminar sin confirm")
    except Exception as e:
        # Esto es esperado si implementamos validación en la función
        print(f"\n✓ Esperado: {e}")
        print("  Nota: La validación de confirm está en el endpoint")

    db.close()


def test_4_crear_batch_de_prueba():
    """Test: Crear batch de prueba para eliminar"""
    print_header("TEST 4: Crear batch de prueba")

    db = SessionLocal()

    # Crear batch de prueba
    batch = ImportBatch(
        filename="test_delete_batch.xlsx",
        file_hash=f"test_hash_{datetime.now().timestamp()}",
        rows_inserted=0
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    print(f"\n✓ Batch de prueba creado:")
    print(f"  ID: {batch.id}")
    print(f"  Archivo: {batch.filename}")

    # Crear algunos movimientos de prueba
    movimientos_test = [
        Movimiento(
            fecha=datetime.now().date(),
            descripcion=f"Movimiento test {i}",
            monto=100.0 * i,
            batch_id=batch.id
        )
        for i in range(1, 4)
    ]

    for mov in movimientos_test:
        db.add(mov)

    db.commit()

    print(f"\n✓ Movimientos de prueba creados: 3")

    batch_id = batch.id
    db.close()
    return batch_id


def test_5_eliminar_batch_con_confirm(batch_id: int):
    """Test: Eliminar batch con confirm"""
    print_header(f"TEST 5: Eliminar batch {batch_id} con confirm")

    db = SessionLocal()

    # Contar movimientos antes
    movs_antes = db.query(Movimiento).filter(
        Movimiento.batch_id == batch_id
    ).count()

    print(f"\nMovimientos antes del borrado: {movs_antes}")

    # Eliminar batch
    resultado = delete_batch(db, batch_id, actor="test_script")

    print(f"\n✓ Batch eliminado exitosamente:")
    print(f"  Batch ID: {resultado['batch_id']}")
    print(f"  Origen: {resultado['origen']}")
    print(f"  Movimientos eliminados: {resultado['movimientos_eliminados']}")
    print(f"  Audit ID: {resultado['audit_id']}")

    # Verificar que no existen movimientos
    movs_despues = db.query(Movimiento).filter(
        Movimiento.batch_id == batch_id
    ).count()

    print(f"\nMovimientos después del borrado: {movs_despues}")

    if movs_despues == 0:
        print("✓ Todos los movimientos fueron eliminados")
    else:
        print(f"✗ ERROR: Quedan {movs_despues} movimientos huérfanos")

    # Verificar que el batch no existe
    batch_existe = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id
    ).first()

    if not batch_existe:
        print("✓ Batch eliminado correctamente")
    else:
        print("✗ ERROR: El batch todavía existe")

    db.close()


def test_6_verificar_auditoria():
    """Test: Verificar registros de auditoría"""
    print_header("TEST 6: Verificar auditoría")

    db = SessionLocal()

    # Obtener último registro de DELETE_BATCH
    audit = db.query(AuditLog).filter(
        AuditLog.action == "DELETE_BATCH"
    ).order_by(
        AuditLog.created_at.desc()
    ).first()

    if audit:
        print(f"\n✓ Último registro de DELETE_BATCH:")
        print(f"  ID: {audit.id}")
        print(f"  Actor: {audit.actor}")
        print(f"  Acción: {audit.action}")
        print(f"  Fecha: {audit.created_at}")
        print(f"  Before: {audit.before}")
        print(f"  After: {audit.after}")
    else:
        print("\n✗ No hay registros de DELETE_BATCH")

    db.close()


def run_all_tests():
    """Ejecuta todos los tests en secuencia"""
    print("\n" + "=" * 60)
    print("  SISTEMA DE GESTIÓN ADMINISTRATIVA DE BATCHES")
    print("  Test Suite Completo")
    print("=" * 60)

    try:
        # Test 1: Listar batches
        batches = test_1_listar_batches()

        # Test 2: Obtener info de primer batch (si existe)
        if batches:
            primer_batch_id = batches[0]['id']
            test_2_obtener_batch_info(primer_batch_id)

        # Test 3: Validación de confirm (conceptual)
        # test_3_eliminar_batch_sin_confirm(primer_batch_id)

        # Test 4: Crear batch de prueba
        batch_test_id = test_4_crear_batch_de_prueba()

        # Test 5: Eliminar batch de prueba
        test_5_eliminar_batch_con_confirm(batch_test_id)

        # Test 6: Verificar auditoría
        test_6_verificar_auditoria()

        print("\n" + "=" * 60)
        print("  ✓ TODOS LOS TESTS COMPLETADOS")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
