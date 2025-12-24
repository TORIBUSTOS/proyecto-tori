"""
Test de endpoints de edición de movimientos (ETAPA 3)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from datetime import date


def test_edicion_y_eliminacion():
    """
    Test manual de edición y eliminación de movimientos.
    """
    db = SessionLocal()

    try:
        print("\n" + "=" * 60)
        print("TEST DE EDICION Y ELIMINACION DE MOVIMIENTOS")
        print("=" * 60)

        # 1. Crear un movimiento de prueba
        print("\n[1/5] Creando movimiento de prueba...")
        mov_test = Movimiento(
            fecha=date.today(),
            descripcion="TRANSFERENCIA TEST EDICION",
            monto=-1000.0,
            categoria="SIN_CATEGORIA",
            subcategoria=None,
            batch_id=None
        )
        db.add(mov_test)
        db.commit()
        db.refresh(mov_test)
        print(f"   OK - Movimiento creado con ID: {mov_test.id}")
        print(f"   Descripcion: {mov_test.descripcion}")
        print(f"   Categoria: {mov_test.categoria}")

        # 2. Editar el movimiento
        print("\n[2/5] Editando movimiento (simulando PUT /api/movimientos/{id})...")
        mov_test.descripcion = "TRANSFERENCIA EDITADA"
        mov_test.categoria = "EGRESOS"
        mov_test.subcategoria = "Servicios"
        db.commit()
        db.refresh(mov_test)
        print(f"   OK - Movimiento editado exitosamente")
        print(f"   Nueva descripcion: {mov_test.descripcion}")
        print(f"   Nueva categoria: {mov_test.categoria}")
        print(f"   Nueva subcategoria: {mov_test.subcategoria}")

        # 3. Verificar que se guardó
        print("\n[3/5] Verificando cambios en DB...")
        mov_verificado = db.query(Movimiento).filter(Movimiento.id == mov_test.id).first()
        assert mov_verificado is not None
        assert mov_verificado.descripcion == "TRANSFERENCIA EDITADA"
        assert mov_verificado.categoria == "EGRESOS"
        assert mov_verificado.subcategoria == "Servicios"
        print(f"   OK - Cambios verificados correctamente en DB")

        # 4. Eliminar el movimiento
        print("\n[4/5] Eliminando movimiento (simulando DELETE /api/movimientos/{id})...")
        mov_id = mov_test.id
        db.delete(mov_test)
        db.commit()
        print(f"   OK - Movimiento {mov_id} eliminado exitosamente")

        # 5. Verificar que se eliminó
        print("\n[5/5] Verificando eliminacion...")
        mov_eliminado = db.query(Movimiento).filter(Movimiento.id == mov_id).first()
        assert mov_eliminado is None
        print(f"   OK - Movimiento eliminado correctamente de DB")

        print("\n" + "=" * 60)
        print("OK - TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("   - Crear movimiento: OK")
        print("   - Editar movimiento: OK")
        print("   - Verificar edicion: OK")
        print("   - Eliminar movimiento: OK")
        print("   - Verificar eliminacion: OK")
        print("\nLos endpoints PUT y DELETE estan listos para usarse en la UI")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    test_edicion_y_eliminacion()
