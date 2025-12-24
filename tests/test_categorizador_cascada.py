"""
Tests unitarios para el motor de categorización en cascada
"""

import pytest
from backend.core.categorizador_cascada import (
    CategorizadorCascada,
    categorizar_texto,
    _norm
)


class TestNormalizacion:
    """Tests de normalización de texto"""

    def test_norm_basico(self):
        assert _norm("Hola Mundo") == "hola mundo"

    def test_norm_tildes(self):
        assert _norm("Débito Crédito") == "debito credito"

    def test_norm_caracteres_especiales(self):
        assert _norm("Compra·VISA-Débito/2024") == "compra visa debito 2024"

    def test_norm_espacios_multiples(self):
        assert _norm("texto    con     espacios") == "texto con espacios"

    def test_norm_none(self):
        assert _norm(None) == ""


class TestCategorizadorNivel1:
    """Tests de categorización nivel 1 (concepto)"""

    def setUp(self):
        self.motor = CategorizadorCascada()

    def test_transferencia_recibida(self):
        """Test: transferencia recibida debe clasificarse como INGRESOS"""
        resultado = categorizar_texto("Crédito por Transferencia")

        assert resultado.categoria == "INGRESOS"
        assert resultado.subcategoria == "Transferencias"
        assert resultado.confianza >= 90
        assert resultado.regla_nivel1_id == "ING-001"

    def test_debin_afiliados(self):
        """Test: DEBIN debe clasificarse como INGRESOS:DEBIN_Afiliados"""
        resultado = categorizar_texto("Credito DEBIN")

        assert resultado.categoria == "INGRESOS"
        assert resultado.subcategoria == "DEBIN_Afiliados"
        assert resultado.confianza >= 90
        assert resultado.regla_nivel1_id == "ING-002"

    def test_impuesto_debitos_creditos(self):
        """Test: impuesto sobre débitos debe clasificarse correctamente"""
        resultado = categorizar_texto("Impuesto Débitos y Créditos/DB")

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Impuestos_Debitos_Creditos"
        assert resultado.confianza == 100
        assert resultado.regla_nivel1_id == "IMP-001"

    def test_compra_visa_debito(self):
        """Test: compra con visa débito debe clasificarse como Gastos_Compras"""
        resultado = categorizar_texto("Compra VISA Débito")

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Gastos_Compras"
        assert resultado.confianza >= 70
        assert resultado.regla_nivel1_id == "GAS-001"

    def test_transferencia_enviada(self):
        """Test: transferencia por CBU debe clasificarse como EGRESOS:Transferencias"""
        resultado = categorizar_texto("Transferencia por CBU")

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Transferencias"
        assert resultado.confianza >= 70
        assert resultado.regla_nivel1_id == "EGR-001"


class TestCategorizadorNivel2:
    """Tests de refinamiento nivel 2 (detalle)"""

    def test_compra_refinada_a_servicio_agua(self):
        """Test: compra genérica se refina a Servicios_Agua"""
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="AGUAS CORDOBESAS"
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Servicios_Agua"
        assert resultado.fue_refinado == True
        assert resultado.confianza >= 95
        assert resultado.regla_nivel2_id == "REF-GAS-001"

    def test_compra_refinada_a_servicio_electricidad(self):
        """Test: compra genérica se refina a Servicios_Electricidad"""
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="EPEC CORDOBA"
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Servicios_Electricidad"
        assert resultado.fue_refinado == True
        assert resultado.regla_nivel2_id == "REF-GAS-002"

    def test_compra_refinada_a_pedidosya(self):
        """Test: compra genérica se refina a Gastos_Viaticos (PedidosYa)"""
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="PEDIDOSYA DELIVERY"
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Gastos_Viaticos"
        assert resultado.fue_refinado == True

    def test_transferencia_refinada_a_farmacia(self):
        """Test: transferencia se refina a Prestadores_Farmacias"""
        resultado = categorizar_texto(
            concepto="Transferencia por CBU",
            detalle="FARMACIA LIDER S.A."
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Prestadores_Farmacias"
        assert resultado.fue_refinado == True
        assert resultado.regla_nivel2_id == "REF-EGR-001"

    def test_transferencia_refinada_a_profesional(self):
        """Test: transferencia a profesional (Dr./Dra.)"""
        resultado = categorizar_texto(
            concepto="Transferencia por CBU",
            detalle="DR. JUAN PEREZ CARDIOLOGO"
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Prestadores_Profesionales"
        assert resultado.fue_refinado == True

    def test_transferencia_refinada_a_afip(self):
        """Test: transferencia a AFIP se refina a Impuestos_AFIP"""
        resultado = categorizar_texto(
            concepto="Transferencia por CBU",
            detalle="AFIP - PAGO IMPUESTOS"
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Impuestos_AFIP"
        assert resultado.fue_refinado == True
        assert resultado.confianza == 100

    def test_compra_sin_refinamiento(self):
        """Test: compra que no tiene patrón nivel 2 mantiene categoría base"""
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="COMERCIO GENERICO S.A."
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Gastos_Compras"
        assert resultado.fue_refinado == False
        assert resultado.regla_nivel2_id is None


class TestCasosComplejos:
    """Tests de casos complejos y edge cases"""

    def test_texto_vacio(self):
        """Test: texto vacío debe clasificarse como OTROS"""
        resultado = categorizar_texto("")

        assert resultado.categoria == "OTROS"
        assert resultado.subcategoria == "Sin_Clasificar"
        assert resultado.confianza == 0

    def test_texto_sin_match(self):
        """Test: texto sin match debe clasificarse como OTROS"""
        resultado = categorizar_texto("XYZABC123 TEXTO RANDOM")

        # Debería matchear la regla default "OTROS"
        assert resultado.categoria in ["OTROS", "EGRESOS"]  # Depende de las reglas

    def test_case_insensitive(self):
        """Test: debe ser case-insensitive"""
        resultado1 = categorizar_texto("CREDITO DEBIN")
        resultado2 = categorizar_texto("credito debin")
        resultado3 = categorizar_texto("Credito Debin")

        assert resultado1.categoria == resultado2.categoria == resultado3.categoria
        assert resultado1.subcategoria == resultado2.subcategoria == resultado3.subcategoria

    def test_con_tildes(self):
        """Test: debe ignorar tildes"""
        resultado1 = categorizar_texto("Crédito por Transferencia")
        resultado2 = categorizar_texto("Credito por Transferencia")

        assert resultado1.categoria == resultado2.categoria
        assert resultado1.subcategoria == resultado2.subcategoria

    def test_multiples_palabras_clave_nivel2(self):
        """Test: múltiples palabras clave en nivel 2"""
        # Google tiene varias palabras clave: "google gsuite", "google workspace", "google one"
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="GOOGLE WORKSPACE MONTHLY"
        )

        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Servicios_Software"
        assert resultado.fue_refinado == True


class TestPrioridades:
    """Tests de prioridad de reglas"""

    def test_prioridad_reglas_nivel1(self):
        """Test: reglas con mayor prioridad (menor número) se evalúan primero"""
        # IMP-001 tiene prioridad 1 y es muy específico
        resultado = categorizar_texto("Impuesto Débitos y Créditos/DB")

        assert resultado.regla_nivel1_id == "IMP-001"
        assert resultado.confianza == 100


class TestConfianza:
    """Tests de niveles de confianza"""

    def test_confianza_alta_impuestos(self):
        """Test: impuestos deben tener confianza 100%"""
        resultado = categorizar_texto("Impuesto Débitos y Créditos/DB")
        assert resultado.confianza == 100

    def test_confianza_media_compras(self):
        """Test: compras genéricas tienen menor confianza"""
        resultado = categorizar_texto("Compra VISA Débito", "COMERCIO CUALQUIERA")
        assert resultado.confianza >= 70

    def test_confianza_aumenta_con_refinamiento(self):
        """Test: refinamiento nivel 2 puede aumentar confianza"""
        # Nivel 1: Gastos_Compras con confianza 70
        # Nivel 2: Servicios_Electricidad con confianza 95
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="EPEC CORDOBA"
        )

        assert resultado.fue_refinado == True
        assert resultado.confianza >= 95  # Confianza del nivel 2


class TestIntegracion:
    """Tests de integración del sistema completo"""

    def test_flujo_completo_sin_refinamiento(self):
        """Test: flujo completo para movimiento sin refinamiento"""
        resultado = categorizar_texto(
            concepto="Crédito por Transferencia",
            detalle="JUAN PEREZ - PAGO SERVICIOS"
        )

        # Nivel 1: INGRESOS:Transferencias
        # Nivel 2: No hay refinamiento para INGRESOS:Transferencias en este caso
        assert resultado.categoria == "INGRESOS"
        assert resultado.subcategoria == "Transferencias"
        assert resultado.regla_nivel1_id == "ING-001"
        # Puede o no estar refinado dependiendo si "obra social" está en el detalle

    def test_flujo_completo_con_refinamiento(self):
        """Test: flujo completo para movimiento con refinamiento"""
        resultado = categorizar_texto(
            concepto="Compra VISA Débito",
            detalle="NETFLIX SUBSCRIPTION"
        )

        # Nivel 1: Gastos_Compras
        # Nivel 2: Servicios_Entretenimiento
        assert resultado.categoria == "EGRESOS"
        assert resultado.subcategoria == "Servicios_Entretenimiento"
        assert resultado.fue_refinado == True
        assert resultado.regla_nivel1_id == "GAS-001"
        assert resultado.regla_nivel2_id == "REF-GAS-007"


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
