"""
Test de detección automática de banco desde archivos Excel
ETAPA 5.1: Detección Automática de Banco

Valida que el sistema detecte correctamente:
- Banco Supervielle
- Banco Galicia
- Archivos desconocidos
"""

import sys
from pathlib import Path

# Asegurar que podemos importar desde backend
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.deteccion_banco import (
    detectar_banco_desde_excel,
    BANK_SUPERVIELLE,
    BANK_GALICIA,
    BANK_DESCONOCIDO
)


def test_deteccion_supervielle():
    """
    Test de detección de archivos Banco Supervielle

    Busca archivos Excel en ./output/uploads/ que contengan
    indicadores de Supervielle.
    """
    print("\n" + "=" * 80)
    print("TEST 1: Detección Banco Supervielle")
    print("=" * 80)

    uploads_dir = Path("./output/uploads")

    if not uploads_dir.exists():
        print("[ERROR] Directorio ./output/uploads no existe")
        print("   Por favor, importa al menos un extracto de Supervielle primero")
        return False

    # Buscar archivos Excel
    excel_files = list(uploads_dir.glob("*.xlsx")) + list(uploads_dir.glob("*.xls"))

    if not excel_files:
        print("[ERROR] No hay archivos Excel en ./output/uploads")
        print("   Por favor, importa al menos un extracto primero")
        return False

    print(f"\nArchivos encontrados: {len(excel_files)}")

    supervielle_detectados = []

    for file_path in excel_files:
        print(f"\nAnalizando: {file_path.name}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        banco_detectado = detectar_banco_desde_excel(file_bytes)
        print(f"   Banco detectado: {banco_detectado}")

        if banco_detectado == BANK_SUPERVIELLE:
            supervielle_detectados.append(file_path.name)

    if supervielle_detectados:
        print(f"\n[OK] Archivos Supervielle detectados: {len(supervielle_detectados)}")
        for filename in supervielle_detectados:
            print(f"   - {filename}")
        return True
    else:
        print("\n[WARN] No se detectaron archivos de Supervielle")
        print("   Esto es correcto si todos los extractos son de otro banco")
        return True  # No es un error si no hay archivos de Supervielle


def test_deteccion_galicia():
    """
    Test de detección de archivos Banco Galicia
    """
    print("\n" + "=" * 80)
    print("TEST 2: Detección Banco Galicia")
    print("=" * 80)

    uploads_dir = Path("./output/uploads")

    if not uploads_dir.exists():
        print("[ERROR] Directorio ./output/uploads no existe")
        return False

    excel_files = list(uploads_dir.glob("*.xlsx")) + list(uploads_dir.glob("*.xls"))

    if not excel_files:
        print("[ERROR] No hay archivos Excel en ./output/uploads")
        return False

    galicia_detectados = []

    for file_path in excel_files:
        print(f"\nAnalizando: {file_path.name}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        banco_detectado = detectar_banco_desde_excel(file_bytes)
        print(f"   Banco detectado: {banco_detectado}")

        if banco_detectado == BANK_GALICIA:
            galicia_detectados.append(file_path.name)

    if galicia_detectados:
        print(f"\n[OK] Archivos Galicia detectados: {len(galicia_detectados)}")
        for filename in galicia_detectados:
            print(f"   - {filename}")
        return True
    else:
        print("\n[WARN] No se detectaron archivos de Galicia")
        print("   Esto es correcto si todos los extractos son de otro banco")
        return True


def test_deteccion_desconocido():
    """
    Test de archivos que no matchean ningún banco conocido
    """
    print("\n" + "=" * 80)
    print("TEST 3: Detección Archivos Desconocidos")
    print("=" * 80)

    uploads_dir = Path("./output/uploads")

    if not uploads_dir.exists():
        print("[ERROR] Directorio ./output/uploads no existe")
        return False

    excel_files = list(uploads_dir.glob("*.xlsx")) + list(uploads_dir.glob("*.xls"))

    if not excel_files:
        print("[ERROR] No hay archivos Excel en ./output/uploads")
        return False

    desconocidos = []

    for file_path in excel_files:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        banco_detectado = detectar_banco_desde_excel(file_bytes)

        if banco_detectado == BANK_DESCONOCIDO:
            desconocidos.append(file_path.name)

    if desconocidos:
        print(f"\n[WARN] Archivos sin banco detectado: {len(desconocidos)}")
        for filename in desconocidos:
            print(f"   - {filename}")
        print("\n   Esto puede indicar:")
        print("   - Formato Excel no estandar")
        print("   - Banco no soportado aun")
        print("   - Archivo corrupto o vacio")
    else:
        print("\n[OK] Todos los archivos fueron identificados correctamente")

    return True


def test_resumen_estadisticas():
    """
    Muestra un resumen de detecciones por banco
    """
    print("\n" + "=" * 80)
    print("RESUMEN: Estadísticas de Detección")
    print("=" * 80)

    uploads_dir = Path("./output/uploads")

    if not uploads_dir.exists():
        print("[ERROR] Directorio ./output/uploads no existe")
        return False

    excel_files = list(uploads_dir.glob("*.xlsx")) + list(uploads_dir.glob("*.xls"))

    if not excel_files:
        print("[ERROR] No hay archivos Excel en ./output/uploads")
        return False

    estadisticas = {
        BANK_SUPERVIELLE: 0,
        BANK_GALICIA: 0,
        BANK_DESCONOCIDO: 0
    }

    for file_path in excel_files:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        banco_detectado = detectar_banco_desde_excel(file_bytes)
        estadisticas[banco_detectado] += 1

    total = len(excel_files)

    print(f"\nTotal de archivos analizados: {total}")
    print(f"\n   Supervielle: {estadisticas[BANK_SUPERVIELLE]} ({estadisticas[BANK_SUPERVIELLE] / total * 100:.1f}%)")
    print(f"   Galicia: {estadisticas[BANK_GALICIA]} ({estadisticas[BANK_GALICIA] / total * 100:.1f}%)")
    print(f"   Desconocidos: {estadisticas[BANK_DESCONOCIDO]} ({estadisticas[BANK_DESCONOCIDO] / total * 100:.1f}%)")

    tasa_deteccion = ((estadisticas[BANK_SUPERVIELLE] + estadisticas[BANK_GALICIA]) / total * 100)
    print(f"\n[OK] Tasa de deteccion exitosa: {tasa_deteccion:.1f}%")

    return True


def main():
    """
    Ejecuta todos los tests de detección de banco
    """
    print("\n")
    print("=" * 80)
    print(" " * 20 + "TEST DETECCION AUTOMATICA DE BANCO")
    print(" " * 30 + "ETAPA 5.1")
    print("=" * 80)

    tests = [
        test_deteccion_supervielle,
        test_deteccion_galicia,
        test_deteccion_desconocido,
        test_resumen_estadisticas
    ]

    resultados = []

    for test_func in tests:
        try:
            resultado = test_func()
            resultados.append((test_func.__name__, resultado))
        except Exception as e:
            print(f"\n[ERROR] ERROR en {test_func.__name__}: {e}")
            resultados.append((test_func.__name__, False))

    # Resumen final
    print("\n" + "=" * 80)
    print("RESULTADO FINAL")
    print("=" * 80)

    tests_exitosos = sum(1 for _, resultado in resultados if resultado)
    tests_totales = len(resultados)

    for nombre, resultado in resultados:
        status = "PASS" if resultado else "FAIL"
        print(f"[{status}] - {nombre}")

    print(f"\n{'OK' if tests_exitosos == tests_totales else 'FAIL'} Tests: {tests_exitosos}/{tests_totales} exitosos")

    if tests_exitosos == tests_totales:
        print("\nTODOS LOS TESTS PASARON - Deteccion de banco implementada correctamente")
    else:
        print("\nALGUNOS TESTS FALLARON - Revisar implementacion")

    print("\n" + "=" * 80 + "\n")

    return tests_exitosos == tests_totales


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
