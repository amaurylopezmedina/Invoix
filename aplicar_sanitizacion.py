#!/usr/bin/env python
"""
Script para aplicar sanitización automática a logs en ufe.py

Aplica sanitize_for_log() a los casos detectados.
"""
import re
from pathlib import Path


def aplicar_sanitizacion_automatica(archivo_path: str = "glib/ufe.py"):
    """
    Aplica sanitización automática a los logs.
    """
    with open(archivo_path, "r", encoding="utf-8") as f:
        contenido = f.read()

    cambios = 0
    contenido_modificado = contenido

    # Patrón 1: rest.LastErrorText
    patron1 = r"log_event\(([^,]+),\s*([^,]+),\s*(rest\.LastErrorText)\s*\)"
    reemplazo1 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron1, reemplazo1, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron1, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 2: gen.LastErrorText
    patron2 = r"log_event\(([^,]+),\s*([^,]+),\s*(gen\.LastErrorText)\s*\)"
    reemplazo2 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron2, reemplazo2, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron2, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 3: verifier.LastErrorText
    patron3 = r"log_event\(([^,]+),\s*([^,]+),\s*(verifier\.LastErrorText)\s*\)"
    reemplazo3 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron3, reemplazo3, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron3, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 4: rest.ResponseHeader
    patron4 = r"log_event\(([^,]+),\s*([^,]+),\s*(rest\.ResponseHeader)\s*\)"
    reemplazo4 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron4, reemplazo4, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron4, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 5: sbResponseBody.GetAsString()
    patron5 = r"log_event\(([^,]+),\s*([^,]+),\s*(sbResponseBody\.GetAsString\(\))\s*\)"
    reemplazo5 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron5, reemplazo5, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron5, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 6: jsonResponse.Emit()
    patron6 = r"log_event\(([^,]+),\s*([^,]+),\s*(jsonResponse\.Emit\(\))\s*\)"
    reemplazo6 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron6, reemplazo6, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron6, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 7: json_response (variable)
    patron7 = r"log_event\(([^,]+),\s*([^,]+),\s*(json_response)\s*\)"
    reemplazo7 = r"log_event(\1, \2, sanitize_for_log(str(\3)))"
    contenido_nuevo = re.sub(patron7, reemplazo7, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron7, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 8: .lastErrorText() (con paréntesis)
    patron8 = r"log_event\(([^,]+),\s*([^,]+),\s*(\w+\.lastErrorText\(\))\s*\)"
    reemplazo8 = r"log_event(\1, \2, sanitize_for_log(\3))"
    contenido_nuevo = re.sub(patron8, reemplazo8, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron8, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 9: response.text
    patron9 = (
        r'log_event\(([^,]+),\s*([^,]+),\s*f"([^"]*)\{(response\.text)\}([^"]*)"\s*\)'
    )
    reemplazo9 = r'log_event(\1, \2, f"\3{sanitize_for_log(\4)}\5"'
    contenido_nuevo = re.sub(patron9, reemplazo9, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron9, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Patrón 10: response.headers
    patron10 = r'log_event\(([^,]+),\s*([^,]+),\s*f"([^"]*)\{(response\.headers)\}([^"]*)"\s*\)'
    reemplazo10 = r'log_event(\1, \2, f"\3{sanitize_for_log(str(\4))}\5"'
    contenido_nuevo = re.sub(patron10, reemplazo10, contenido_modificado)
    if contenido_nuevo != contenido_modificado:
        cambios += len(re.findall(patron10, contenido_modificado))
        contenido_modificado = contenido_nuevo

    # Guardar archivo modificado
    if cambios > 0:
        with open(archivo_path, "w", encoding="utf-8") as f:
            f.write(contenido_modificado)
        print(f"✅ Archivo modificado: {cambios} sanitizaciones aplicadas")
        return cambios
    else:
        print("ℹ️  No se encontraron cambios para aplicar")
        return 0


if __name__ == "__main__":
    print("=" * 80)
    print("APLICANDO SANITIZACIÓN AUTOMÁTICA A LOGS")
    print("=" * 80)
    print()

    cambios = aplicar_sanitizacion_automatica()

    if cambios > 0:
        print()
        print(
            "🔄 Ejecute 'python verificar_sanitizacion.py' para ver el progreso actualizado"
        )

    print("=" * 80)
