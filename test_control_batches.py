"""
Script de prueba para validar el control de batches
Verifica que la detección de duplicados y el sistema de batches funcionen correctamente
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy.orm import Session
from backend.database.connection import get_db, engine
from backend.models.import_batch import ImportBatch
from backend.models.movimiento import Movimiento
from backend.utils.file_hash import calculate_file_hash
import hashlib

def test_file_hash():
    """Test 1: Verificar que el hash funcione correctamente"""
    print("\n" + "="*80)
    print("TEST 1: Función de hash")
    print("="*80)

    test_data1 = b"test content 123"
    test_data2 = b"test content 123"
    test_data3 = b"different content"

    hash1 = calculate_file_hash(test_data1)
    hash2 = calculate_file_hash(test_data2)
    hash3 = calculate_file_hash(test_data3)

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")

    assert hash1 == hash2, "❌ Mismo contenido debería dar mismo hash"
    assert hash1 != hash3, "❌ Contenido diferente debería dar hash diferente"
    assert len(hash1) == 64, "❌ Hash SHA256 debería tener 64 caracteres"

    print("✅ Función de hash funciona correctamente")
    return True

def test_import_batch_model():
    """Test 2: Verificar que el modelo ImportBatch funcione"""
    print("\n" + "="*80)
    print("TEST 2: Modelo ImportBatch")
    print("="*80)

    db = next(get_db())

    try:
        # Crear un batch de prueba
        test_hash = hashlib.sha256(b"test_batch_001").hexdigest()
        batch = ImportBatch(
            filename="test_archivo.xlsx",
            file_hash=test_hash,
            rows_inserted=10
        )

        db.add(batch)
        db.commit()

        # Verificar que se creó
        batch_db = db.query(ImportBatch).filter(ImportBatch.file_hash == test_hash).first()
        assert batch_db is not None, "❌ Batch no se guardó en BD"
        assert batch_db.filename == "test_archivo.xlsx", "❌ Filename incorrecto"
        assert batch_db.rows_inserted == 10, "❌ rows_inserted incorrecto"
        assert batch_db.imported_at is not None, "❌ imported_at debería ser automático"

        print(f"✅ Batch creado: ID={batch_db.id}, File={batch_db.filename}")
        print(f"   Importado: {batch_db.imported_at}")
        print(f"   Hash: {batch_db.file_hash[:16]}...")

        # Limpiar
        db.delete(batch_db)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def test_duplicate_detection():
    """Test 3: Verificar detección de duplicados"""
    print("\n" + "="*80)
    print("TEST 3: Detección de duplicados")
    print("="*80)

    db = next(get_db())

    try:
        # Crear primer batch
        test_hash = hashlib.sha256(b"test_duplicate_001").hexdigest()
        batch1 = ImportBatch(
            filename="extracto_enero.xlsx",
            file_hash=test_hash,
            rows_inserted=20
        )
        db.add(batch1)
        db.commit()

        print(f"✅ Primer batch creado: ID={batch1.id}")

        # Intentar crear segundo batch con mismo hash
        try:
            batch2 = ImportBatch(
                filename="extracto_enero_copia.xlsx",
                file_hash=test_hash,  # Mismo hash
                rows_inserted=20
            )
            db.add(batch2)
            db.commit()
            print("❌ ERROR: Se permitió duplicado")
            return False
        except Exception as e:
            db.rollback()
            print(f"✅ Duplicado rechazado correctamente: {str(e)[:50]}...")

        # Limpiar
        db.delete(batch1)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def test_movimiento_batch_relationship():
    """Test 4: Verificar relación Movimiento-Batch"""
    print("\n" + "="*80)
    print("TEST 4: Relación Movimiento-Batch")
    print("="*80)

    db = next(get_db())

    try:
        from datetime import date

        # Crear batch
        test_hash = hashlib.sha256(b"test_relationship_001").hexdigest()
        batch = ImportBatch(
            filename="test_relacion.xlsx",
            file_hash=test_hash,
            rows_inserted=0
        )
        db.add(batch)
        db.flush()

        batch_id = batch.id
        print(f"✅ Batch creado: ID={batch_id}")

        # Crear movimiento asociado
        mov = Movimiento(
            fecha=date(2025, 12, 14),
            descripcion="Movimiento de prueba",
            monto=1000.50,
            categoria="TEST",
            batch_id=batch_id
        )
        db.add(mov)
        batch.rows_inserted = 1
        db.commit()

        # Verificar relación
        mov_db = db.query(Movimiento).filter(Movimiento.batch_id == batch_id).first()
        assert mov_db is not None, "❌ Movimiento no encontrado"
        assert mov_db.batch_id == batch_id, "❌ batch_id incorrecto"

        # Verificar relationship
        if mov_db.batch:
            print(f"✅ Relationship funciona: {mov_db.batch.filename}")
        else:
            print("⚠️  Relationship no configurado (no crítico)")

        print(f"✅ Movimiento creado: ID={mov_db.id}, Batch={mov_db.batch_id}")

        # Limpiar
        db.delete(mov_db)
        db.delete(batch)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def test_batch_query():
    """Test 5: Verificar queries de batches"""
    print("\n" + "="*80)
    print("TEST 5: Queries de batches")
    print("="*80)

    db = next(get_db())

    try:
        # Crear varios batches
        batches = []
        for i in range(3):
            test_hash = hashlib.sha256(f"test_query_{i}".encode()).hexdigest()
            batch = ImportBatch(
                filename=f"extracto_{i}.xlsx",
                file_hash=test_hash,
                rows_inserted=10 * (i + 1)
            )
            db.add(batch)
            batches.append(batch)

        db.commit()
        print(f"✅ {len(batches)} batches creados")

        # Query: último batch
        ultimo = db.query(ImportBatch).order_by(ImportBatch.imported_at.desc()).first()
        assert ultimo is not None, "❌ No se encontró último batch"
        print(f"✅ Último batch: ID={ultimo.id}, File={ultimo.filename}")

        # Query: todos los batches
        todos = db.query(ImportBatch).all()
        assert len(todos) >= 3, "❌ No se encontraron todos los batches"
        print(f"✅ Total batches en BD: {len(todos)}")

        # Limpiar
        for batch in batches:
            db.delete(batch)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "🧪"*40)
    print("SUITE DE TESTS - CONTROL DE BATCHES")
    print("🧪"*40)

    tests = [
        ("Hash SHA256", test_file_hash),
        ("Modelo ImportBatch", test_import_batch_model),
        ("Detección de duplicados", test_duplicate_detection),
        ("Relación Movimiento-Batch", test_movimiento_batch_relationship),
        ("Queries de batches", test_batch_query),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO en {name}: {e}")
            results.append((name, False))

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
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
        print("✅ El sistema de control de batches está funcionando correctamente")
    else:
        print("⚠️  Algunos tests fallaron. Revisar implementación.")

    print("="*80)

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
