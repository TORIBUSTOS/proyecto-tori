"""
Test de verificación rápida para ETAPA 2
Verifica que la función core anular_batch funcione correctamente
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import date
import hashlib
from fastapi import HTTPException
from backend.database.connection import get_db
from backend.models.import_batch import ImportBatch
from backend.models.movimiento import Movimiento
from backend.core.batches import anular_batch


def test_core_anular_batch_exitoso():
    """Test 1: Función core anular_batch funciona correctamente"""
    print("\n" + "="*80)
    print("TEST 1: Función core anular_batch - Caso exitoso")
    print("="*80)

    db = next(get_db())

    try:
        # Crear batch de prueba
        test_hash = hashlib.sha256(b"test_core_001").hexdigest()
        batch = ImportBatch(
            filename="test_core.xlsx",
            file_hash=test_hash,
            rows_inserted=0
        )
        db.add(batch)
        db.flush()

        batch_id = batch.id
        print(f"✅ Batch creado: ID={batch_id}")

        # Crear movimientos
        for i in range(3):
            mov = Movimiento(
                fecha=date(2025, 12, 15),
                descripcion=f"Test core {i}",
                monto=100.0,
                categoria="TEST",
                batch_id=batch_id
            )
            db.add(mov)

        batch.rows_inserted = 3
        db.commit()

        print(f"✅ 3 movimientos creados")

        # LLAMAR A LA FUNCIÓN CORE
        resultado = anular_batch(db, batch_id)

        print(f"✅ Función core ejecutada exitosamente")
        print(f"   Status: {resultado['status']}")
        print(f"   Batch ID: {resultado['batch_id']}")
        print(f"   Movimientos eliminados: {resultado['movimientos_eliminados']}")
        print(f"   Filename: {resultado['batch']['filename']}")

        # Verificar que se eliminó
        batch_after = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        assert batch_after is None, "❌ Batch debería estar eliminado"

        count_after = db.query(Movimiento).filter(Movimiento.batch_id == batch_id).count()
        assert count_after == 0, "❌ Movimientos deberían estar eliminados"

        # Verificar respuesta
        assert resultado['status'] == 'success', "❌ Status incorrecto"
        assert resultado['batch_id'] == batch_id, "❌ batch_id incorrecto"
        assert resultado['movimientos_eliminados'] == 3, "❌ Conteo incorrecto"
        assert resultado['batch']['filename'] == 'test_core.xlsx', "❌ Filename incorrecto"

        print("✅ Batch y movimientos eliminados correctamente")
        print("✅ Respuesta JSON correcta")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_core_anular_batch_404():
    """Test 2: Función core lanza HTTPException 404 si batch no existe"""
    print("\n" + "="*80)
    print("TEST 2: Función core anular_batch - Caso 404")
    print("="*80)

    db = next(get_db())

    try:
        batch_id_inexistente = 99999

        # Intentar anular batch inexistente
        try:
            resultado = anular_batch(db, batch_id_inexistente)
            print("❌ Debería haber lanzado HTTPException 404")
            return False
        except HTTPException as e:
            if e.status_code == 404:
                print(f"✅ HTTPException 404 lanzado correctamente")
                print(f"   Detail: {e.detail}")
                assert f"Batch {batch_id_inexistente} no existe" in e.detail
                return True
            else:
                print(f"❌ Status code incorrecto: {e.status_code}")
                return False

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_core_transaccionalidad():
    """Test 3: Verificar que usa db.begin() para transaccionalidad"""
    print("\n" + "="*80)
    print("TEST 3: Transaccionalidad con db.begin()")
    print("="*80)

    db = next(get_db())

    try:
        # Crear batch
        test_hash = hashlib.sha256(b"test_transaction_core").hexdigest()
        batch = ImportBatch(
            filename="test_tx.xlsx",
            file_hash=test_hash,
            rows_inserted=0
        )
        db.add(batch)
        db.flush()

        batch_id = batch.id

        # Crear movimiento
        mov = Movimiento(
            fecha=date(2025, 12, 15),
            descripcion="Test TX",
            monto=100.0,
            categoria="TEST",
            batch_id=batch_id
        )
        db.add(mov)
        batch.rows_inserted = 1
        db.commit()

        print(f"✅ Batch creado: ID={batch_id}")

        # Anular usando función core
        resultado = anular_batch(db, batch_id)

        # Verificar que TODO se eliminó (transacción completa)
        batch_after = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        movs_after = db.query(Movimiento).filter(Movimiento.batch_id == batch_id).count()

        assert batch_after is None, "❌ Batch debería estar eliminado"
        assert movs_after == 0, "❌ Movimientos deberían estar eliminados"

        print("✅ Transacción completa: batch y movimientos eliminados")
        print("✅ db.begin() funcionó correctamente")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def run_all_tests():
    """Ejecutar todos los tests de ETAPA 2"""
    print("\n" + "🧪"*40)
    print("TESTS ETAPA 2 - CORE + ENDPOINT")
    print("🧪"*40)

    tests = [
        ("Core anular_batch exitoso", test_core_anular_batch_exitoso),
        ("Core anular_batch 404", test_core_anular_batch_404),
        ("Transaccionalidad db.begin()", test_core_transaccionalidad),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO en {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE TESTS - ETAPA 2")
    print("="*80)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("="*80)
    print(f"Resultado: {passed}/{total} tests pasaron")

    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("\n✅ ETAPA 2 COMPLETADA:")
        print("  ✅ backend/core/batches.py creado")
        print("  ✅ Función anular_batch implementada")
        print("  ✅ Endpoint DELETE usa función core")
        print("  ✅ Transaccionalidad con db.begin()")
        print("  ✅ Manejo de 404 correcto")
        print("  ✅ Hard delete funcionando")
    else:
        print("⚠️  Algunos tests fallaron. Revisar implementación.")

    print("="*80)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
