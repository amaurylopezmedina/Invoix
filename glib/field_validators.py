# field_validators.py
from decimal import Decimal
from typing import Any, Dict
from base_validators import BaseValidator
from validation_types import (
    ValidationResult, VALID_TIPO_INGRESOS, VALID_TIPO_PAGO,
    VALID_FORMA_PAGO, VALID_TIPO_CUENTA_PAGO, VALID_MONEDAS,
    VALID_INDICADOR_FACTURACION
)

class FieldValidator(BaseValidator):
    def validate_encabezado(self, encabezado: Dict[str, Any]) -> ValidationResult:
        """Validates all encabezado fields"""
        # Version validation
        if encabezado.get('Version') != '1.0':
            return "Invalid Version. Must be 1.0"

        # TipoECF validation
        tipo_ecf = encabezado.get('TipoECF')
        if not self.validate_tipo_ecf(tipo_ecf):
            return self.validate_tipo_ecf(tipo_ecf)

        # eNCF validation
        encf = encabezado.get('eNCF', '').strip()
        if not (len(encf) == 13 and encf.isalnum()):
            return "Invalid eNCF format"

        # Validate dates
        fecha_venc = encabezado.get('FechaVencimientoSecuencia')
        if fecha_venc and not self.validate_date(fecha_venc):
            return self.validate_date(fecha_venc)

        return True

    def validate_emisor(self, emisor: Dict[str, Any]) -> ValidationResult:
        """Validates emisor section fields"""
        # RNCEmisor validation
        rnc_result = self.validate_rnc(emisor.get('RNCEmisor', ''))
        if rnc_result is not True:
            return rnc_result

        # RazonSocialEmisor validation
        razon_social = emisor.get('RazonSocialEmisor', '')
        if not self.validate_string_length(razon_social, 150):
            return "RazonSocialEmisor length invalid"

        # Phone validations
        for i in range(1, 4):
            phone = emisor.get(f'TelefonoEmisor{i}')
            if phone and not self.validate_phone(phone):
                return f"Invalid TelefonoEmisor{i} format"

        # Email validation
        email = emisor.get('CorreoEmisor')
        if email and not self.validate_email(email):
            return "Invalid CorreoEmisor format"

        return True

    def validate_comprador(self, comprador: Dict[str, Any]) -> ValidationResult:
        """Validates comprador section fields"""
        # RNCComprador validation
        rnc = comprador.get('RNCComprador')
        if rnc and not self.validate_rnc(rnc):
            return "Invalid RNCComprador format"

        # Email validation
        email = comprador.get('CorreoComprador')
        if email and not self.validate_email(email):
            return "Invalid CorreoComprador format"

        # Phone validation
        phone = comprador.get('TelefonoAdicional')
        if phone and not self.validate_phone(phone):
            return "Invalid TelefonoAdicional format"

        return True

    def validate_totales(self, totales: Dict[str, Any]) -> ValidationResult:
        """Validates totales section fields"""
        # MontoTotal validation
        monto_total = totales.get('MontoTotal')
        if monto_total is not None:
            result = self.validate_decimal(monto_total, 18, 2, Decimal('0'))
            if result is not True:
                return "Invalid MontoTotal: " + str(result)

        # ITBIS validations
        for i in range(1, 4):
            itbis = totales.get(f'ITBIS{i}')
            if itbis is not None:
                result = self.validate_decimal(itbis, 18, 2, Decimal('0'))
                if result is not True:
                    return f"Invalid ITBIS{i}: " + str(result)

        return True

    def validate_detalle_item(self, item: Dict[str, Any]) -> ValidationResult:
        """Validates individual item details"""
        # NumeroLinea validation
        numero_linea = item.get('NumeroLinea')
        if not (1 <= numero_linea <= 1000):
            return "NumeroLinea must be between 1 and 1000"

        # CantidadItem validation
        cantidad = item.get('CantidadItem')
        if cantidad is not None:
            result = self.validate_decimal(cantidad, 18, 2, Decimal('0'))
            if result is not True:
                return "Invalid CantidadItem: " + str(result)

        # PrecioUnitarioItem validation
        precio = item.get('PrecioUnitarioItem')
        if precio is not None:
            result = self.validate_decimal(precio, 20, 4, Decimal('0'))
            if result is not True:
                return "Invalid PrecioUnitarioItem: " + str(result)

        return True

    def validate_impuestos_adicionales(self, impuestos: Dict[str, Any]) -> ValidationResult:
        """Validates impuestos adicionales"""
        tipo_impuesto = impuestos.get('TipoImpuesto')
        if tipo_impuesto and not (1 <= int(tipo_impuesto) <= 39):
            return "Invalid TipoImpuesto"

        monto = impuestos.get('MontoImpuestoAdicional')
        if monto is not None:
            result = self.validate_decimal(monto, 18, 2, Decimal('0'))
            if result is not True:
                return "Invalid MontoImpuestoAdicional: " + str(result)

        return True