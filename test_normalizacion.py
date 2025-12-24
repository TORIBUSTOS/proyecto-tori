"""
Test de normalización de columnas
"""
import re
import unicodedata

def _norm_col(s: str) -> str:
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Test con las columnas del Excel
columnas_excel = ["Fecha", "Concepto", "Detalle", "Débito", "Crédito", "Saldo"]

print("Columnas originales -> normalizadas:")
for col in columnas_excel:
    print(f"  '{col}' -> '{_norm_col(col)}'")

# Test con aliases
aliases_debito = ["debito", "debitos", "debe", "debit"]
print("\nAliases de debito normalizados:")
for alias in aliases_debito:
    print(f"  '{alias}' -> '{_norm_col(alias)}'")

# Verificar si hay match
norm_debito = _norm_col("Débito")
norm_aliases = [_norm_col(x) for x in aliases_debito]

print(f"\n¿'{norm_debito}' está en {norm_aliases}?")
print(f"  Respuesta: {norm_debito in norm_aliases}")
