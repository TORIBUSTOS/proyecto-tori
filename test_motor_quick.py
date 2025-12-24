"""Quick test del motor de categorización"""
import sys
sys.path.insert(0, '.')

from backend.core.categorizador_cascada import categorizar_texto

tests = [
    ("Credito por Transferencia", "", "Transferencia recibida"),
    ("Credito DEBIN", "", "DEBIN afiliado"),
    ("Transferencia por CBU", "FARMACIA LIDER", "Transferencia a farmacia"),
    ("Compra VISA Debito", "PEDIDOSYA", "Compra en PedidosYa"),
    ("Compra VISA Debito", "EPEC CORDOBA", "Pago luz EPEC"),
    ("Compra VISA Debito", "NETFLIX", "Suscripción Netflix"),
    ("Impuesto Debitos y Creditos/DB", "", "Impuesto bancario"),
    ("Pago de Servicios", "AFIP", "Pago AFIP"),
    ("Transferencia por CBU", "DR. JUAN PEREZ", "Pago a profesional"),
]

print("=" * 70)
print("TESTS DE CATEGORIZACIÓN - Motor Cascada v2.0")
print("=" * 70)
print()

for concepto, detalle, descripcion in tests:
    resultado = categorizar_texto(concepto, detalle)

    print(f"{descripcion}:")
    print(f"  Concepto: {concepto}")
    if detalle:
        print(f"  Detalle: {detalle}")
    print(f"  > {resultado.categoria} > {resultado.subcategoria}")
    print(f"  Confianza: {resultado.confianza}%")

    if resultado.fue_refinado:
        print(f"  [*] Refinado en nivel 2 (regla: {resultado.regla_nivel2_id})")
    else:
        print(f"  [-] Solo nivel 1 (regla: {resultado.regla_nivel1_id})")

    print()

print("=" * 70)
print("TESTS COMPLETADOS")
print("=" * 70)
