from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from datetime import datetime

def cargar_certificado(ruta_p12: str, clave: str):
    """Carga un archivo .p12 y devuelve los datos relevantes"""
    with open(ruta_p12, "rb") as f:
        p12_data = f.read()

    private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
        p12_data,
        clave.encode() if clave else None,
        backend=default_backend()
    )

    info = []
    if certificate:
        subject = certificate.subject
        issuer = certificate.issuer

        info.append("===== CERTIFICADO PRINCIPAL =====")
        info.append("Sujeto (Subject):")
        for attr in subject:
            info.append(f"  {attr.oid._name}: {attr.value}")

        info.append("\nEmisor (Issuer):")
        for attr in issuer:
            info.append(f"  {attr.oid._name}: {attr.value}")

        info.append(f"\nNúmero de serie: {certificate.serial_number}")
        info.append(f"Válido desde: {certificate.not_valid_before}")
        info.append(f"Válido hasta: {certificate.not_valid_after}")

        # Validación de vigencia
        ahora = datetime.utcnow()
        if certificate.not_valid_before <= ahora <= certificate.not_valid_after:
            estado = "✅ Vigente"
        else:
            estado = "❌ Expirado"
        info.append(f"Estado: {estado}")

        info.append(f"\nAlgoritmo de firma: {certificate.signature_algorithm_oid._name}")

    # Estado de la clave privada
    info.append("\n===== ESTADO DE LA CLAVE PRIVADA =====")
    info.append("Clave privada: " + ("Cargada correctamente" if private_key else "No encontrada"))

    # Certificados adicionales
    info.append("\n===== CERTIFICADOS ADICIONALES =====")
    if additional_certs:
        for i, cert in enumerate(additional_certs, 1):
            info.append(f"Certificado adicional #{i} -> Sujeto: {cert.subject.rfc4514_string()}")
    else:
        info.append("No se encontraron certificados adicionales.")

    return "\n".join(info)
