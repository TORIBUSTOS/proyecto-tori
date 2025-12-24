"""
Test de lectura del Excel real
"""
import pandas as pd
import re
import unicodedata

def _norm_col(s: str) -> str:
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Leer el Excel
excel_path = r"C:\Users\mauri\OneDrive\Escritorio\CLAUDE\sanarte_financiero_web\output\uploads\20251214_183006_Movimientos_Supervielle_NOVIEMBRE.xlsx"

try:
    df = pd.read_excel(excel_path)

    print("=== COLUMNAS ORIGINALES (sin normalizar) ===")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. '{col}' (tipo: {type(col).__name__})")

    print("\n=== COLUMNAS NORMALIZADAS ===")
    col_map = {c: _norm_col(str(c)) for c in df.columns}
    for orig, norm in col_map.items():
        print(f"'{orig}' -> '{norm}'")

    # Renombrar
    df = df.rename(columns=col_map)
    norm_cols = set(df.columns)

    print(f"\n=== SET DE COLUMNAS NORMALIZADAS ===")
    print(sorted(list(norm_cols)))

    # Probar aliases
    ALIASES = {
        "debito": ["debito", "debitos", "debe", "debit", "egreso", "cargo"],
        "credito": ["credito", "creditos", "haber", "credit", "ingreso", "abono"],
    }

    print(f"\n=== PRUEBA DE MATCHING ===")
    for k, opts in ALIASES.items():
        normalized_opts = [_norm_col(x) for x in opts]
        print(f"\nBuscando '{k}':")
        print(f"  Opciones normalizadas: {normalized_opts}")

        for opt in normalized_opts:
            if opt in norm_cols:
                print(f"  ✓ MATCH encontrado: '{opt}'")
                break
        else:
            print(f"  ✗ NO MATCH")

except FileNotFoundError:
    print(f"Archivo no encontrado. Buscando en uploads...")
    import os
    uploads = r"C:\Users\mauri\OneDrive\Escritorio\CLAUDE\sanarte_financiero_web\output\uploads"
    if os.path.exists(uploads):
        files = [f for f in os.listdir(uploads) if f.endswith('.xlsx')]
        print(f"Archivos encontrados: {files}")
        if files:
            latest = max(files)
            print(f"\nUsando: {latest}")
            df = pd.read_excel(os.path.join(uploads, latest))
            print(f"Columnas: {list(df.columns)}")
