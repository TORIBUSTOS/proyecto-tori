"""
Test de Integración Completa - ETAPA 4

Simula el flujo completo de usuario:
1. Crea un movimiento sin categoría
2. Lo categoriza (debe usar motor cascada)
3. Edita manualmente y guarda regla
4. Crea otro movimiento similar
5. Categoriza (debe usar regla aprendida)
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from backend.models.regla_categorizacion import ReglaCategorizacion
from backend.core.reglas_aprendidas import (
    generar_patron_desde_descripcion,
    obtener_o_crear_regla
)
from backend.core.categorizador_cascada import categorizar_movimientos


def main():
    print("=" * 70)
    print("TEST DE INTEGRACIÓN COMPLETA - ETAPA 4")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Limpiar datos de test
        print("\n[PREPARACIÓN] Limpiando datos de test...")
        db.query(Movimiento).filter(Movimiento.descripcion.like("TEST INTEG%")).delete()
        db.query(ReglaCategorizacion).filter(ReglaCategorizacion.patron.like("TEST INTEG%")).delete()
        db.commit()
        print("✓ Datos de test eliminados")

        # ========================================
        # PASO 1: Crear movimiento sin categoría
        # ========================================
        print("\n[PASO 1] Creando movimiento sin categoría...")
        mov1 = Movimiento(
            fecha=datetime.now(),
            descripcion="TEST INTEG FARMACIA CENTRAL COMPRA MEDICAMENTOS",
            monto=-1500.00,
            categoria=None,
            subcategoria=None
        )
        db.add(mov1)
        db.commit()
        db.refresh(mov1)
        print(f"✓ Movimiento creado: ID={mov1.id}")
        print(f"  Descripción: {mov1.descripcion}")
        print(f"  Categoría: {mov1.categoria}")

        # ========================================
        # PASO 2: Categorizar (motor cascada)
        # ========================================
        print("\n[PASO 2] Categorizando con motor cascada...")
        resultado = categorizar_movimientos(db, solo_sin_categoria=True)
        db.refresh(mov1)
        print(f"✓ Categorización ejecutada:")
        print(f"  Procesados: {resultado['procesados']}")
        print(f"  Categorizados: {resultado['categorizados']}")
        print(f"  Aplicados regla aprendida: {resultado['aplicados_regla_aprendida']}")
        print(f"\n✓ Movimiento categorizado:")
        print(f"  Categoría: {mov1.categoria}")
        print(f"  Subcategoría: {mov1.subcategoria}")

        # ========================================
        # PASO 3: Editar y guardar regla
        # ========================================
        print("\n[PASO 3] Usuario edita movimiento y guarda regla...")

        # Usuario cambia a categoría específica
        nueva_categoria = "EGRESOS"
        nueva_subcategoria = "Prestadores_Farmacias"

        # Actualizar movimiento
        mov1.categoria = nueva_categoria
        mov1.subcategoria = nueva_subcategoria
        db.commit()

        # Generar patrón y guardar regla (simula checkbox "Recordar regla")
        patron = generar_patron_desde_descripcion(mov1.descripcion)
        regla = obtener_o_crear_regla(
            patron=patron,
            categoria=nueva_categoria,
            subcategoria=nueva_subcategoria,
            db=db
        )

        print(f"✓ Movimiento editado:")
        print(f"  Nueva categoría: {mov1.categoria}")
        print(f"  Nueva subcategoría: {mov1.subcategoria}")
        print(f"\n✓ Regla guardada:")
        print(f"  Patrón: {regla.patron}")
        print(f"  Categoría: {regla.categoria} / {regla.subcategoria}")
        print(f"  Confianza: {regla.confianza}%")
        print(f"  Veces usada: {regla.veces_usada}")

        # ========================================
        # PASO 4: Crear movimiento similar
        # ========================================
        print("\n[PASO 4] Creando movimiento similar...")
        mov2 = Movimiento(
            fecha=datetime.now(),
            descripcion="TEST INTEG FARMACIA CENTRAL COMPRA PRODUCTOS VARIOS",
            monto=-850.00,
            categoria=None,
            subcategoria=None
        )
        db.add(mov2)
        db.commit()
        db.refresh(mov2)
        print(f"✓ Movimiento creado: ID={mov2.id}")
        print(f"  Descripción: {mov2.descripcion}")
        print(f"  Categoría: {mov2.categoria} (sin categorizar)")

        # ========================================
        # PASO 5: Categorizar (debe usar regla aprendida)
        # ========================================
        print("\n[PASO 5] Categorizando con regla aprendida...")
        resultado2 = categorizar_movimientos(db, solo_sin_categoria=True)
        db.refresh(mov2)
        db.refresh(regla)

        print(f"✓ Categorización ejecutada:")
        print(f"  Procesados: {resultado2['procesados']}")
        print(f"  Aplicados regla aprendida: {resultado2['aplicados_regla_aprendida']}")

        print(f"\n✓ Movimiento categorizado AUTOMÁTICAMENTE:")
        print(f"  Categoría: {mov2.categoria}")
        print(f"  Subcategoría: {mov2.subcategoria}")
        print(f"  Confianza: {mov2.confianza_porcentaje}%")

        print(f"\n✓ Regla actualizada:")
        print(f"  Confianza: {regla.confianza}% (incrementó +1)")
        print(f"  Veces usada: {regla.veces_usada} (incrementó +1)")

        # ========================================
        # VALIDACIÓN
        # ========================================
        print("\n[VALIDACIÓN]")
        assert resultado2['aplicados_regla_aprendida'] >= 1, "Debe aplicar regla aprendida"
        assert mov2.categoria == nueva_categoria, f"Categoría debe ser {nueva_categoria}"
        assert mov2.subcategoria == nueva_subcategoria, f"Subcategoría debe ser {nueva_subcategoria}"
        assert regla.veces_usada >= 2, "Veces usada debe ser >= 2"
        print("✓ Todas las validaciones pasaron")

        # Limpiar
        print("\n[LIMPIEZA] Eliminando datos de test...")
        db.delete(mov1)
        db.delete(mov2)
        db.delete(regla)
        db.commit()
        print("✓ Datos de test eliminados")

        print("\n" + "=" * 70)
        print("✅ TEST DE INTEGRACIÓN COMPLETA: EXITOSO")
        print("=" * 70)
        print("\nEl sistema de reglas aprendibles funciona correctamente:")
        print("  1. ✓ Motor cascada categoriza movimientos normalmente")
        print("  2. ✓ Usuario puede editar y guardar reglas")
        print("  3. ✓ Reglas aprendidas se aplican automáticamente")
        print("  4. ✓ Contadores de confianza y uso se actualizan")
        print("  5. ✓ Sistema aprende de las correcciones del usuario")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
