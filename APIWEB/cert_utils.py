"""
Utilidades para manejar certificados digitales .p12/.pfx
Extraer información de validez y otros datos del certificado
"""

import json
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from datetime import datetime


def cargar_certificado(ruta_p12: str, clave: str, como_json=True):
    """Carga un archivo .p12 y devuelve los datos como JSON o dict"""
    with open(ruta_p12, "rb") as f:
        p12_data = f.read()

    private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
        p12_data,
        clave.encode() if clave else None,
        backend=default_backend()
    )

    data = {
        "certificado_principal": {},
        "estado_clave_privada": "No encontrada",
        "certificados_adicionales": []
    }

    if certificate:
        subject = {attr.oid._name: attr.value for attr in certificate.subject}
        issuer = {attr.oid._name: attr.value for attr in certificate.issuer}

        ahora = datetime.utcnow()
        dias_restantes = (certificate.not_valid_after - ahora).days

        if ahora > certificate.not_valid_after:
            estado = "Expirado"
        elif dias_restantes <= 30:
            estado = "Próximo a vencerse"
        else:
            estado = "Vigente"

        data["certificado_principal"] = {
            "subject": subject,
            "issuer": issuer,
            "numero_serie": str(certificate.serial_number),
            "valido_desde": certificate.not_valid_before.isoformat(),
            "valido_hasta": certificate.not_valid_after.isoformat(),
            "estado": estado,
            "algoritmo_firma": certificate.signature_algorithm_oid._name,
        }

    if private_key:
        data["estado_clave_privada"] = "Cargada correctamente"

    if additional_certs:
        for cert in additional_certs:
            data["certificados_adicionales"].append({
                "subject": {attr.oid._name: attr.value for attr in cert.subject},
                "issuer": {attr.oid._name: attr.value for attr in cert.issuer},
                "numero_serie": str(cert.serial_number),
                "valido_desde": cert.not_valid_before.isoformat(),
                "valido_hasta": cert.not_valid_after.isoformat()
            })

    return json.dumps(data, indent=4, ensure_ascii=False) if como_json else data


def resumen_validez(ruta_p12: str, clave: str, como_json=True):
    """Devuelve solo valido_desde, valido_hasta y estado (Vigente / Próximo a vencerse / Expirado)"""
    with open(ruta_p12, "rb") as f:
        p12_data = f.read()

    _, certificate, _ = pkcs12.load_key_and_certificates(
        p12_data,
        clave.encode() if clave else None,
        backend=default_backend()
    )

    if not certificate:
        raise ValueError("No se encontró certificado principal en el archivo .p12")

    ahora = datetime.utcnow()
    dias_restantes = (certificate.not_valid_after - ahora).days

    if ahora > certificate.not_valid_after:
        estado = "Expirado"
    elif dias_restantes <= 30:
        estado = "Próximo a vencerse"
    else:
        estado = "Vigente"

    data = {
        "valido_desde": certificate.not_valid_before.isoformat(),
        "valido_hasta": certificate.not_valid_after.isoformat(),
        "estado": estado,
        "dias_restantes": dias_restantes
    }

    return json.dumps(data, indent=4, ensure_ascii=False) if como_json else data


def obtener_info_basica_certificado(ruta_p12: str, clave: str):
    """
    Obtiene información básica del certificado sin necesidad de parsear todo.
    Devuelve un diccionario con valido_desde, valido_hasta, estado y días restantes.
    """
    try:
        return resumen_validez(ruta_p12, clave, como_json=False)
    except Exception as e:
        return {
            "valido_desde": None,
            "valido_hasta": None,
            "estado": "error",
            "dias_restantes": None,
            "error": str(e)
        }
