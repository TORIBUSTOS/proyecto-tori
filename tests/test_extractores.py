"""
Tests unitarios para extractores de metadata.

Verifica que cada extractor funcione correctamente con casos reales
extraídos de movimientos bancarios del sistema TORO.
"""

import pytest
from backend.core.extractores import (
    extraer_nombre,
    extraer_documento,
    es_debin,
    extraer_debin_id,
    extraer_cbu,
    extraer_terminal,
    extraer_comercio,
    extraer_referencia,
    extraer_metadata_completa
)


class TestExtraerNombre:
    """Tests para extraer_nombre()"""

    def test_transferencia_persona_fisica(self):
        """Debe extraer nombre de persona física en transferencia"""
        detalle = "Crédito por Transferencia - CONCEPTO: Transferencia recibida TERMINAL: MBSP0001 NOMBRE: DORADO GABRIELA BEATRIZ DOCUMENTO: 12345678"
        assert extraer_nombre(detalle) == "DORADO GABRIELA BEATRIZ"

    def test_transferencia_persona_con_coma(self):
        """Debe manejar nombres con formato APELLIDO, NOMBRE"""
        detalle = "TERMINAL: LINK0012100C5 NOMBRE: FIGUEROA, CLAUDIO MAXI DOCUMENTO: 20123456"
        assert extraer_nombre(detalle) == "FIGUEROA, CLAUDIO MAXI"

    def test_transferencia_con_barra(self):
        """Debe manejar nombres con barra diagonal"""
        detalle = "NOMBRE: SANTUCHO/PABLO OSCA DOCUMENTO: 20123456"
        assert extraer_nombre(detalle) == "SANTUCHO/PABLO OSCA"

    def test_debin_empresa(self):
        """Debe extraer razón social de empresa"""
        detalle = "Credito DEBIN - LEYENDA: Transferencia recibida TIPO_DEBIN: 05 NOMBRE: SANARTE SRL DOCUMENTO: 30712384960"
        assert extraer_nombre(detalle) == "SANARTE SRL"

    def test_sin_nombre(self):
        """Debe retornar None si no encuentra nombre"""
        detalle = "Compra Visa Débito - COMERCIO: PEDIDOSYA PROPINAS OPERACION: 982948"
        assert extraer_nombre(detalle) is None

    def test_string_vacio(self):
        """Debe manejar string vacío"""
        assert extraer_nombre("") is None

    def test_none(self):
        """Debe manejar None"""
        assert extraer_nombre(None) is None


class TestExtraerDocumento:
    """Tests para extraer_documento()"""

    def test_dni_8_digitos(self):
        """Debe extraer DNI de 8 dígitos"""
        detalle = "NOMBRE: JUAN PEREZ DOCUMENTO: 12345678"
        assert extraer_documento(detalle) == "12345678"

    def test_cuil_11_digitos(self):
        """Debe extraer CUIL/CUIT de 11 dígitos"""
        detalle = "NOMBRE: SANARTE SRL DOCUMENTO: 30712384960"
        assert extraer_documento(detalle) == "30712384960"

    def test_documento_con_id(self):
        """Debe extraer documento con formato ID: (débitos automáticos)"""
        detalle = "Débito Automático de Servicio - AFIP ID:30712384960 PRES:PLANRG4667"
        assert extraer_documento(detalle) == "30712384960"

    def test_sin_documento(self):
        """Debe retornar None si no encuentra documento"""
        detalle = "Compra Visa Débito - COMERCIO: PEDIDOSYA"
        assert extraer_documento(detalle) is None

    def test_documento_invalido(self):
        """Debe ignorar números que no sean 8 u 11 dígitos"""
        detalle = "DOCUMENTO: 123"  # 3 dígitos, inválido
        # El regex solo matchea 8-11 dígitos, así que debería ser None
        assert extraer_documento(detalle) is None


class TestEsDebin:
    """Tests para es_debin()"""

    def test_debito_debin(self):
        """Debe detectar débito DEBIN"""
        concepto = "Debito DEBIN"
        detalle = "CONCEPTO_QB: 8 LEYENDA: Transferencia enviada TIPO_DEBIN: 04"
        assert es_debin(concepto, detalle) is True

    def test_credito_debin(self):
        """Debe detectar crédito DEBIN"""
        concepto = "Credito DEBIN"
        detalle = "LEYENDA: Transferencia recibida TIPO_DEBIN: 05"
        assert es_debin(concepto, detalle) is True

    def test_debin_en_detalle(self):
        """Debe detectar DEBIN aunque solo esté en detalle"""
        concepto = ""
        detalle = "ID_DEBIN: L18M NOMBRE: SANARTE"
        assert es_debin(concepto, detalle) is True

    def test_no_es_debin(self):
        """Debe retornar False si no es DEBIN"""
        concepto = "Transferencia por CBU"
        detalle = "CONCEPTO: Transferencia enviada"
        assert es_debin(concepto, detalle) is False

    def test_case_insensitive(self):
        """Debe ser case-insensitive"""
        concepto = "debito debin"
        detalle = ""
        assert es_debin(concepto, detalle) is True

    def test_ambos_vacios(self):
        """Debe retornar False si ambos son vacíos"""
        assert es_debin("", "") is False

    def test_ambos_none(self):
        """Debe retornar False si ambos son None"""
        assert es_debin(None, None) is False


class TestExtraerDebinId:
    """Tests para extraer_debin_id()"""

    def test_debin_id_numerico_largo(self):
        """Debe extraer ID numérico largo"""
        detalle = "ID_DEBIN: 2512010000125350751512 DOCUMENTO: 123"
        assert extraer_debin_id(detalle) == "2512010000125350751512"

    def test_debin_id_alfanumerico_corto(self):
        """Debe extraer ID alfanumérico corto"""
        detalle = "ID_DEBIN: L18M NOMBRE: SANARTE"
        assert extraer_debin_id(detalle) == "L18M"

    def test_debin_id_codigo_corto(self):
        """Debe extraer códigos cortos"""
        detalle = "ID_DEBIN: WY7Z DOCUMENTO: 30712384960"
        assert extraer_debin_id(detalle) == "WY7Z"

    def test_sin_debin_id(self):
        """Debe retornar None si no encuentra ID_DEBIN"""
        detalle = "Transferencia por CBU sin DEBIN"
        assert extraer_debin_id(detalle) is None


class TestExtraerCBU:
    """Tests para extraer_cbu()"""

    def test_cbu_22_digitos(self):
        """Debe extraer CBU de 22 dígitos"""
        detalle = "CBU: 0070076430004136307784 DOCUMENTO: 123"
        assert extraer_cbu(detalle) == "0070076430004136307784"

    def test_otro_cbu(self):
        """Debe extraer otro CBU válido"""
        detalle = "CBU: 4530000800013309377553"
        assert extraer_cbu(detalle) == "4530000800013309377553"

    def test_sin_cbu(self):
        """Debe retornar None si no encuentra CBU"""
        detalle = "Transferencia sin CBU"
        assert extraer_cbu(detalle) is None

    def test_cbu_incompleto(self):
        """Debe ignorar CBU con menos de 22 dígitos"""
        detalle = "CBU: 123456"  # Solo 6 dígitos
        assert extraer_cbu(detalle) is None


class TestExtraerTerminal:
    """Tests para extraer_terminal()"""

    def test_terminal_standard(self):
        """Debe extraer terminal standard"""
        detalle = "TERMINAL: MBSP0001 NOMBRE: JUAN"
        assert extraer_terminal(detalle) == "MBSP0001"

    def test_terminal_link(self):
        """Debe extraer terminal LINK"""
        detalle = "TERMINAL: LINK0012100C5"
        assert extraer_terminal(detalle) == "LINK0012100C5"

    def test_terminal_tesp(self):
        """Debe extraer terminal TESP"""
        detalle = "TERMINAL: TESP0000 CBU: 123"
        assert extraer_terminal(detalle) == "TESP0000"

    def test_sin_terminal(self):
        """Debe retornar None si no encuentra terminal"""
        detalle = "Compra sin terminal"
        assert extraer_terminal(detalle) is None


class TestExtraerComercio:
    """Tests para extraer_comercio()"""

    def test_comercio_pedidosya(self):
        """Debe extraer nombre de comercio PedidosYa"""
        detalle = "Compra Visa Débito - COMERCIO: PEDIDOSYA PROPINAS OPERACION: 982948"
        assert extraer_comercio(detalle) == "PEDIDOSYA PROPINAS"

    def test_comercio_con_asterisco(self):
        """Debe manejar comercios con asterisco"""
        detalle = "COMERCIO: OPENAI *CHATGPT SUBSCR OPERACION: 779574"
        assert extraer_comercio(detalle) == "OPENAI *CHATGPT SUBSCR"

    def test_comercio_con_guion(self):
        """Debe manejar comercios con guión"""
        detalle = "COMERCIO: PAGOS360*EPEC OPERACION: 553497"
        assert extraer_comercio(detalle) == "PAGOS360*EPEC"

    def test_comercio_sin_operacion(self):
        """Debe extraer comercio aunque no tenga OPERACION al final"""
        detalle = "COMERCIO: FARMACIA LIDER"
        assert extraer_comercio(detalle) == "FARMACIA LIDER"

    def test_sin_comercio(self):
        """Debe retornar None si no encuentra comercio"""
        detalle = "Transferencia sin comercio"
        assert extraer_comercio(detalle) is None


class TestExtraerReferencia:
    """Tests para extraer_referencia()"""

    def test_referencia_servicio_agua(self):
        """Debe extraer referencia de servicio de agua"""
        detalle = "AGUAS CORDOBESAS ID:467017 PRES:SERV AGUA REF:01569339387"
        assert extraer_referencia(detalle) == "01569339387"

    def test_referencia_gas(self):
        """Debe extraer referencia de gas"""
        detalle = "D.GAS DEL CENTRO ID:21067746 PRES:GASCENTRO REF:FC2811-67404620"
        assert extraer_referencia(detalle) == "FC2811-67404620"

    def test_referencia_afip(self):
        """Debe extraer referencia AFIP"""
        detalle = "AFIP ID:30712384960 PRES:PLANRG4667 REF:R4667N500541063"
        assert extraer_referencia(detalle) == "R4667N500541063"

    def test_sin_referencia(self):
        """Debe retornar None si no encuentra referencia"""
        detalle = "Compra sin referencia"
        assert extraer_referencia(detalle) is None


class TestExtraerMetadataCompleta:
    """Tests para extraer_metadata_completa()"""

    def test_transferencia_completa(self):
        """Debe extraer toda la metadata de una transferencia"""
        concepto = "Crédito por Transferencia"
        detalle = "CONCEPTO: Transferencia recibida TERMINAL: MBSP0001 NOMBRE: DORADO GABRIELA BEATRIZ DOCUMENTO: 12345678"

        result = extraer_metadata_completa(concepto, detalle)

        assert result['persona_nombre'] == "DORADO GABRIELA BEATRIZ"
        assert result['documento'] == "12345678"
        assert result['es_debin'] is False
        assert result['debin_id'] is None
        assert result['terminal'] == "MBSP0001"

    def test_debin_completo(self):
        """Debe extraer toda la metadata de un DEBIN"""
        concepto = "Credito DEBIN"
        detalle = "LEYENDA: Transferencia recibida TIPO_DEBIN: 05 NOMBRE: SANARTE SRL DOCUMENTO: 30712384960 ID_DEBIN: L18M"

        result = extraer_metadata_completa(concepto, detalle)

        assert result['persona_nombre'] == "SANARTE SRL"
        assert result['documento'] == "30712384960"
        assert result['es_debin'] is True
        assert result['debin_id'] == "L18M"

    def test_compra_comercio(self):
        """Debe extraer metadata de compra en comercio"""
        concepto = "Compra Visa Débito"
        detalle = "COMERCIO: OPENAI *CHATGPT SUBSCR OPERACION: 779574"

        result = extraer_metadata_completa(concepto, detalle)

        assert result['persona_nombre'] is None
        assert result['documento'] is None
        assert result['es_debin'] is False
        assert result['comercio'] == "OPENAI *CHATGPT SUBSCR"

    def test_debito_automatico(self):
        """Debe extraer metadata de débito automático"""
        concepto = "Débito Automático de Servicio"
        detalle = "AGUAS CORDOBESAS ID:467017 PRES:SERV AGUA REF:01569339387"

        result = extraer_metadata_completa(concepto, detalle)

        # El ID solo se extrae si tiene 8 u 11 dígitos (CUIT/DNI)
        # 467017 tiene solo 6 dígitos, así que no matchea
        assert result['documento'] is None
        assert result['referencia'] == "01569339387"
        assert result['es_debin'] is False

    def test_movimiento_sin_metadata(self):
        """Debe manejar movimiento sin metadata extraíble"""
        concepto = "Impuesto Débitos y Créditos/DB"
        detalle = ""

        result = extraer_metadata_completa(concepto, detalle)

        assert result['persona_nombre'] is None
        assert result['documento'] is None
        assert result['es_debin'] is False
        assert result['debin_id'] is None
        assert result['cbu'] is None
        assert result['terminal'] is None
        assert result['comercio'] is None
        assert result['referencia'] is None


# ============================================================================
# Tests de casos edge y robustez
# ============================================================================

class TestCasosEdge:
    """Tests de casos edge y robustez"""

    def test_texto_mixto_mayusculas_minusculas(self):
        """Debe manejar texto con mayúsculas/minúsculas mezcladas"""
        detalle = "nombre: Juan Perez documento: 12345678"
        # El regex es case-insensitive para la palabra clave "NOMBRE:"
        # Pero captura el contenido tal cual aparece (mixto en este caso)
        assert extraer_nombre(detalle) == "Juan Perez"

    def test_multiples_espacios(self):
        """Debe limpiar múltiples espacios en nombres"""
        detalle = "NOMBRE: JUAN    PEREZ   GOMEZ DOCUMENTO: 123"
        nombre = extraer_nombre(detalle)
        assert nombre == "JUAN PEREZ GOMEZ"  # Espacios normalizados

    def test_texto_con_acentos(self):
        """Debe manejar texto con acentos"""
        detalle = "NOMBRE: JOSÉ MARÍA PÉREZ DOCUMENTO: 123"
        assert extraer_nombre(detalle) == "JOSÉ MARÍA PÉREZ"

    def test_extractores_no_rompen_con_none(self):
        """Ningún extractor debe lanzar excepción con None"""
        assert extraer_nombre(None) is None
        assert extraer_documento(None) is None
        assert extraer_debin_id(None) is None
        assert extraer_cbu(None) is None
        assert extraer_terminal(None) is None
        assert extraer_comercio(None) is None
        assert extraer_referencia(None) is None

    def test_extractores_no_rompen_con_vacio(self):
        """Ningún extractor debe lanzar excepción con string vacío"""
        assert extraer_nombre("") is None
        assert extraer_documento("") is None
        assert extraer_debin_id("") is None
        assert extraer_cbu("") is None
        assert extraer_terminal("") is None
        assert extraer_comercio("") is None
        assert extraer_referencia("") is None


if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v"])
