"""
Script para procesar múltiples archivos Excel desde la carpeta input/
Procesa automáticamente todos los archivos .xlsx encontrados
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from backend.database.connection import get_db
from backend.core.consolidar import consolidar_excel
from backend.core.categorizador_cascada import categorizar_movimientos

def procesar_archivos_input():
    """Procesa todos los archivos Excel en la carpeta input/"""

    input_dir = Path(__file__).parent / "input"

    if not input_dir.exists():
        print("[ERROR] No existe la carpeta input/")
        return

    # Buscar archivos Excel
    archivos = sorted(input_dir.glob("*.xlsx"))

    if not archivos:
        print("[WARN] No hay archivos .xlsx en la carpeta input/")
        return

    print("=" * 80)
    print(f"PROCESANDO {len(archivos)} ARCHIVOS DESDE input/")
    print("=" * 80)

    db = next(get_db())
    resultados = []

    for i, archivo in enumerate(archivos, 1):
        print(f"\n[{i}/{len(archivos)}] Procesando: {archivo.name}")
        print("-" * 80)

        try:
            # Leer archivo
            with open(archivo, 'rb') as f:
                contenido = f.read()

            # 1. Consolidar
            r_consolidar = consolidar_excel(contenido, archivo.name, db)

            # 2. Categorizar
            r_cat = categorizar_movimientos(db, solo_sin_categoria=True) or {}

            print(f"[OK] {archivo.name} procesado exitosamente")
            print(f"  - Batch ID: {r_consolidar.get('batch_id')}")
            print(f"  - Movimientos: {r_consolidar.get('insertados', 0)}")
            print(f"  - Categorizados: {r_cat.get('categorizados', 0)}")

            resultados.append({
                "archivo": archivo.name,
                "exito": True,
                "batch_id": r_consolidar.get('batch_id'),
                "movimientos": r_consolidar.get('insertados', 0)
            })

        except Exception as e:
            print(f"[ERROR] Fallo al procesar {archivo.name}: {e}")
            import traceback
            traceback.print_exc()
            resultados.append({
                "archivo": archivo.name,
                "exito": False,
                "error": str(e)
            })

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)

    exitosos = sum(1 for r in resultados if r["exito"])
    fallidos = len(resultados) - exitosos

    print(f"\nArchivos procesados: {len(resultados)}")
    print(f"  - Exitosos: {exitosos}")
    print(f"  - Fallidos: {fallidos}")

    if exitosos > 0:
        print(f"\n[OK] Archivos procesados exitosamente:")
        for r in resultados:
            if r["exito"]:
                print(f"  - {r['archivo']}: Batch {r['batch_id']} con {r['movimientos']} movimientos")

    if fallidos > 0:
        print(f"\n[ERROR] Archivos con errores:")
        for r in resultados:
            if not r["exito"]:
                print(f"  - {r['archivo']}: {r['error']}")

    print("\n" + "=" * 80)
    print("[INFO] Proceso completado")
    print("=" * 80)

    db.close()

if __name__ == "__main__":
    procesar_archivos_input()
