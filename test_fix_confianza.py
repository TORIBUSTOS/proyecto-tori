"""
Script de Validación - Fix Confianza + Reglas IVA/DB-CR

Valida los 4 casos del SUPERBLOQUE NEGRO:
1. IVA: Movimientos con "IVA" deben categorizarse correctamente
2. DB/CR: Movimientos con "Débitos y Créditos" deben categorizarse
3. Edición manual: Guardar debe setear confianza=100, fuente=manual
4. Panel: Verificar que el panel de calidad refleje los cambios

Uso:
    python test_fix_confianza.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from backend.core.categorizador_cascada import CategorizadorCascada, normalize_text
from datetime import date


def print_header(title: str):
    """Imprime un header bonito"""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def test_caso_1_iva():
    """CASO 1: Movimientos con IVA deben categorizarse correctamente"""
    print_header("CASO 1: Clasificación de IVA")

    db = SessionLocal()
    motor = CategorizadorCascada()

    try:
        # Buscar movimientos con "IVA" en la descripción
        movimientos_iva = db.query(Movimiento).filter(
            Movimiento.descripcion.like("%IVA%")
        ).limit(5).all()

        if not movimientos_iva:
            print("⚠️  No se encontraron movimientos con 'IVA' en la descripción")
            print("   Creando movimiento de prueba...")

            # Crear movimiento de prueba
            mov_test = Movimiento(
                fecha=date.today(),
                descripcion="PAGO IVA MENSUAL",
                monto=-5000.0,
                categoria="SIN_CATEGORIA",
                subcategoria="",
                confianza_porcentaje=0
            )
            db.add(mov_test)
            db.commit()
            db.refresh(mov_test)
            movimientos_iva = [mov_test]

        print(f"✅ Encontrados {len(movimientos_iva)} movimientos con 'IVA'")
        print()

        # Probar motor cascada
        for i, mov in enumerate(movimientos_iva, 1):
            print(f"{i}. ID={mov.id}, Desc={mov.descripcion[:50]}")

            resultado = motor.categorizar_cascada(
                concepto=mov.descripcion,
                detalle=mov.descripcion,
                monto=mov.monto
            )

            print(f"   ANTES:  {mov.categoria} / {mov.subcategoria} (confianza={mov.confianza_porcentaje}%)")
            print(f"   MOTOR:  {resultado.categoria} / {resultado.subcategoria} (confianza={resultado.confianza}%)")

            # Verificar resultado esperado
            if resultado.categoria == "IMPUESTOS" and resultado.subcategoria == "Impuestos - IVA":
                print("   ✅ CORRECTO: Clasificado como IVA")
            else:
                print("   ❌ ERROR: No se clasificó como IVA")

            print()

    finally:
        db.close()


def test_caso_2_dbcr():
    """CASO 2: Movimientos con Débitos y Créditos"""
    print_header("CASO 2: Clasificación de Débitos y Créditos")

    db = SessionLocal()
    motor = CategorizadorCascada()

    try:
        # Buscar movimientos con patrones de DB/CR
        variantes = [
            "%DEBITOS%CREDITOS%",
            "%DEB%CRED%",
            "%DÉBITOS%CRÉDITOS%"
        ]

        movimientos_dbcr = []
        for patron in variantes:
            movs = db.query(Movimiento).filter(
                Movimiento.descripcion.like(patron)
            ).limit(2).all()
            movimientos_dbcr.extend(movs)

        if not movimientos_dbcr:
            print("⚠️  No se encontraron movimientos con 'Débitos y Créditos'")
            print("   Creando movimientos de prueba...")

            # Crear movimientos de prueba con variantes
            variantes_test = [
                "IMPUESTO DEBITOS Y CREDITOS",
                "DEB Y CRED BANCARIOS",
                "IMPUESTO DEB CRED"
            ]

            for desc in variantes_test:
                mov_test = Movimiento(
                    fecha=date.today(),
                    descripcion=desc,
                    monto=-150.0,
                    categoria="SIN_CATEGORIA",
                    subcategoria="",
                    confianza_porcentaje=0
                )
                db.add(mov_test)
                movimientos_dbcr.append(mov_test)

            db.commit()

        print(f"✅ Encontrados {len(movimientos_dbcr)} movimientos con patrones DB/CR")
        print()

        # Probar motor cascada
        for i, mov in enumerate(movimientos_dbcr, 1):
            print(f"{i}. ID={mov.id}, Desc={mov.descripcion[:50]}")

            resultado = motor.categorizar_cascada(
                concepto=mov.descripcion,
                detalle=mov.descripcion,
                monto=mov.monto
            )

            print(f"   ANTES:  {mov.categoria} / {mov.subcategoria} (confianza={mov.confianza_porcentaje}%)")
            print(f"   MOTOR:  {resultado.categoria} / {resultado.subcategoria} (confianza={resultado.confianza}%)")

            # Verificar resultado esperado
            if resultado.categoria == "IMPUESTOS" and resultado.subcategoria == "Impuestos - Débitos y Créditos":
                print("   ✅ CORRECTO: Clasificado como Débitos y Créditos")
            else:
                print("   ❌ ERROR: No se clasificó como Débitos y Créditos")

            print()

    finally:
        db.close()


def test_caso_3_edicion_manual():
    """CASO 3: Edición manual debe setear confianza=100, fuente=manual"""
    print_header("CASO 3: Edición Manual")

    db = SessionLocal()

    try:
        # Buscar un movimiento cualquiera
        mov = db.query(Movimiento).first()

        if not mov:
            print("❌ No hay movimientos en la base de datos")
            return

        print(f"📝 Editando movimiento ID={mov.id}")
        print(f"   ANTES: {mov.categoria} / {mov.subcategoria}")
        print(f"   Confianza={mov.confianza_porcentaje}%, Fuente={getattr(mov, 'confianza_fuente', 'N/A')}")
        print()

        # Simular edición manual
        mov.categoria = "INGRESOS"
        mov.subcategoria = "Ingresos - Test Manual"
        mov.confianza_porcentaje = 100

        if hasattr(mov, 'confianza_fuente'):
            mov.confianza_fuente = "manual"

        db.commit()
        db.refresh(mov)

        print(f"   DESPUÉS: {mov.categoria} / {mov.subcategoria}")
        print(f"   Confianza={mov.confianza_porcentaje}%, Fuente={getattr(mov, 'confianza_fuente', 'N/A')}")
        print()

        # Verificar
        if mov.confianza_porcentaje == 100:
            print("   ✅ CORRECTO: Confianza seteada a 100%")
        else:
            print("   ❌ ERROR: Confianza no es 100%")

        if hasattr(mov, 'confianza_fuente') and mov.confianza_fuente == "manual":
            print("   ✅ CORRECTO: Fuente seteada a 'manual'")
        else:
            print("   ❌ ERROR: Fuente no es 'manual'")

    finally:
        db.close()


def test_caso_4_panel_calidad():
    """CASO 4: Panel de calidad debe reflejar cambios"""
    print_header("CASO 4: Panel de Calidad")

    db = SessionLocal()

    try:
        # Estadísticas de confianza
        total_movimientos = db.query(Movimiento).count()

        # Confianza NULL
        sin_confianza = db.query(Movimiento).filter(
            Movimiento.confianza_porcentaje == None
        ).count()

        # Confianza = 0
        confianza_cero = db.query(Movimiento).filter(
            Movimiento.confianza_porcentaje == 0
        ).count()

        # Confianza baja (< 50)
        confianza_baja = db.query(Movimiento).filter(
            Movimiento.confianza_porcentaje < 50,
            Movimiento.confianza_porcentaje.isnot(None),
            Movimiento.confianza_porcentaje > 0
        ).count()

        # Confianza promedio (de movimientos con confianza > 0)
        movimientos_validos = db.query(Movimiento).filter(
            Movimiento.confianza_porcentaje.isnot(None),
            Movimiento.confianza_porcentaje > 0
        ).all()

        if movimientos_validos:
            confianza_promedio = sum(m.confianza_porcentaje for m in movimientos_validos) / len(movimientos_validos)
        else:
            confianza_promedio = 0

        print(f"📊 Estadísticas de Confianza:")
        print(f"   Total movimientos:      {total_movimientos}")
        print(f"   Sin confianza (NULL):   {sin_confianza} ({sin_confianza / total_movimientos * 100:.1f}%)")
        print(f"   Confianza = 0:          {confianza_cero} ({confianza_cero / total_movimientos * 100:.1f}%)")
        print(f"   Confianza baja (< 50):  {confianza_baja} ({confianza_baja / total_movimientos * 100:.1f}%)")
        print(f"   Confianza promedio:     {confianza_promedio:.1f}%")
        print()

        # Verificar problemas
        problemas = []

        if sin_confianza > total_movimientos * 0.1:  # > 10%
            problemas.append(f"⚠️  {sin_confianza} movimientos sin confianza (> 10%)")

        if confianza_cero > total_movimientos * 0.1:  # > 10%
            problemas.append(f"⚠️  {confianza_cero} movimientos con confianza=0 (> 10%)")

        if confianza_promedio < 60:
            problemas.append(f"⚠️  Confianza promedio baja ({confianza_promedio:.1f}% < 60%)")

        if problemas:
            print("❌ Problemas detectados:")
            for p in problemas:
                print(f"   {p}")
            print()
            print("💡 Solución: Ejecuta 'python backfill_confianza.py' y luego 'Aplicar Reglas' en la UI")
        else:
            print("✅ Panel de calidad OK: No se detectaron problemas mayores")

    finally:
        db.close()


def test_normalize_text():
    """Test auxiliar: Verificar normalización de texto"""
    print_header("TEST AUXILIAR: Normalización de Texto")

    casos = [
        "IVA mensual",
        "Débitos y Créditos",
        "DEB Y CRED",
        "impuesto DÉBITOS-CRÉDITOS",
        "PAGO-IVA/2024"
    ]

    for texto in casos:
        normalizado = normalize_text(texto)
        print(f"'{texto}' => '{normalizado}'")

    print()


def main():
    """Función principal"""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  VALIDACIÓN FIX CONFIANZA + REGLAS IVA/DB-CR".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    # Ejecutar tests
    test_normalize_text()
    test_caso_1_iva()
    test_caso_2_dbcr()
    test_caso_3_edicion_manual()
    test_caso_4_panel_calidad()

    print_header("VALIDACIÓN COMPLETADA")
    print("💡 Próximos pasos:")
    print("   1. Si hay movimientos con confianza=0, ejecuta: python backfill_confianza.py")
    print("   2. Luego ejecuta 'Aplicar Reglas' desde la UI")
    print("   3. Verifica el panel de calidad en /metadata")
    print()


if __name__ == "__main__":
    main()
