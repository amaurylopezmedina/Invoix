"""
Tests unitarios para validaciones de seguridad en ufe.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal

import pytest

from glib.ufe import (
    sanitize_filename,
    sanitize_for_log,
    validar_encf,
    validar_montos_factura,
    validar_rnc,
)


class TestValidarRNC:
    """Tests para validación de RNC."""

    def test_rnc_valido_9_digitos(self):
        es_valido, msg = validar_rnc("123456789")
        assert es_valido is True
        assert "válido" in msg.lower()

    def test_rnc_valido_11_digitos(self):
        es_valido, msg = validar_rnc("12345678901")
        assert es_valido is True

    def test_rnc_invalido_letras(self):
        es_valido, msg = validar_rnc("ABC123456")
        assert es_valido is False
        assert "formato inválido" in msg.lower()

    def test_rnc_invalido_longitud(self):
        es_valido, msg = validar_rnc("12345")
        assert es_valido is False

    def test_rnc_todo_ceros(self):
        es_valido, msg = validar_rnc("000000000")
        assert es_valido is False
        assert "ceros" in msg.lower()

    def test_rnc_vacio(self):
        es_valido, msg = validar_rnc("")
        assert es_valido is False
        assert "vacío" in msg.lower()


class TestValidarENCF:
    """Tests para validación de eNCF."""

    def test_encf_valido_31(self):
        es_valido, msg = validar_encf("E310000000001")
        assert es_valido is True

    def test_encf_valido_32(self):
        es_valido, msg = validar_encf("E320000000001")
        assert es_valido is True

    def test_encf_tipo_invalido(self):
        es_valido, msg = validar_encf("E990000000001")
        assert es_valido is False
        assert "inválido" in msg.lower()

    def test_encf_sin_E_inicial(self):
        es_valido, msg = validar_encf("x310000000001")
        assert es_valido is False
        assert "comenzar con 'E'" in msg

    def test_encf_longitud_incorrecta(self):
        es_valido, msg = validar_encf("E31000000")
        assert es_valido is False
        assert "13 caracteres" in msg

    def test_encf_secuencia_cero(self):
        es_valido, msg = validar_encf("E310000000000")
        assert es_valido is False
        assert "000000000" in msg or "cero" in msg.lower()

    def test_encf_tipo_esperado_correcto(self):
        es_valido, msg = validar_encf("E310000000001", tipo_esperado=31)
        assert es_valido is True

    def test_encf_tipo_esperado_incorrecto(self):
        es_valido, msg = validar_encf("E310000000001", tipo_esperado=32)
        assert es_valido is False
        assert "esperado 32" in msg.lower()


class TestValidarMontos:
    """Tests para validación de montos."""

    def test_montos_coherentes(self):
        es_valido, msg = validar_montos_factura(
            "31", Decimal("100.00"), Decimal("18.00"), Decimal("118.00")
        )
        assert es_valido is True

    def test_montos_incoherentes(self):
        es_valido, msg = validar_montos_factura(
            "31",
            Decimal("100.00"),
            Decimal("18.00"),
            Decimal("200.00"),  # Total incorrecto
        )
        assert es_valido is False
        assert "incoherente" in msg.lower()

    def test_monto_negativo(self):
        es_valido, msg = validar_montos_factura(
            "31", Decimal("-100.00"), Decimal("18.00"), Decimal("118.00")
        )
        assert es_valido is False
        assert "negativos" in msg.lower()

    def test_consumo_mayor_250k_no_resumen(self):
        es_valido, msg = validar_montos_factura(
            "32",
            Decimal("250000.00"),
            Decimal("45000.00"),
            Decimal("295000.00"),
            es_resumen=True,
        )
        assert es_valido is False
        assert "250,000" in msg

    def test_descuento_mayor_subtotal(self):
        es_valido, msg = validar_montos_factura(
            "31",
            Decimal("100.00"),
            Decimal("18.00"),
            Decimal("0.00"),
            descuento=Decimal("50.00"),  # Descuento < subtotal pero invalida coherencia
        )
        assert es_valido is False
        assert "monto" in msg.lower() or "coherencia" in msg.lower()


class TestSanitizacion:
    """Tests para funciones de sanitización."""

    def test_sanitize_log_token(self):
        result = sanitize_for_log("Bearer abc123def456")
        assert "abc123def456" not in result
        assert "REDACTED" in result

    def test_sanitize_log_password(self):
        result = sanitize_for_log("password=secret123")
        assert "secret123" not in result
        assert "REDACTED" in result

    def test_sanitize_log_rnc(self):
        result = sanitize_for_log("RNC: 123456789")
        assert "123456789" not in result
        assert "12345" in result  # Muestra primeros dígitos
        assert "*" in result

    def test_sanitize_filename_path_traversal(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result == "etcpasswd"

    def test_sanitize_filename_caracteres_invalidos(self):
        result = sanitize_filename("file<>name.xml")
        assert "<" not in result
        assert ">" not in result
        assert result == "filename.xml"

    def test_sanitize_filename_longitud_maxima(self):
        result = sanitize_filename("a" * 300, max_length=255)
        assert len(result) <= 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
