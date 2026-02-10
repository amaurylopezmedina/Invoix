#!/usr/bin/env python
"""
Script de verificación de sanitización de logs en ufe.py

Verifica qué log_event() contienen datos sensibles sin sanitizar.
"""
import re
from pathlib import Path


def verificar_sanitizacion(archivo_path: str = "glib/ufe.py"):
    """
    Verifica la sanitización de logs en el archivo.

    Returns:
        Tuple[int, int, list]: (logs_sanitizados, logs_sin_sanitizar, casos_sin_sanitizar)
    """
    with open(archivo_path, "r", encoding="utf-8") as f:
        contenido = f.read()
        lineas = contenido.split("\n")

    # Patrones que requieren sanitización
    patrones_sensibles = [
        (r"log_event\([^)]*LastErrorText\s*\)", "LastErrorText sin sanitizar"),
        (r"log_event\([^)]*ResponseHeader\s*\)", "ResponseHeader sin sanitizar"),
        (r"log_event\([^)]*ResponseBody\s*\)", "ResponseBody sin sanitizar"),
        (r"log_event\([^)]*\.GetAsString\(\)\s*\)", "GetAsString sin sanitizar"),
        (r"log_event\([^)]*\.Emit\(\)\s*\)", "Emit sin sanitizar"),
        (r"log_event\([^)]*\.text\s*\)", "response.text sin sanitizar"),
        (r"log_event\([^)]*\.headers\s*\)", "headers sin sanitizar"),
        (r'log_event\([^)]*f".*{url.*}"', "URL sin sanitizar"),
        (r"log_event\([^)]*bearer.*token", "Token sin sanitizar (bearer)"),
    ]

    logs_sin_sanitizar = []
    logs_sanitizados = 0

    for num_linea, linea in enumerate(lineas, start=1):
        # Verificar si contiene log_event
        if "log_event" not in linea:
            continue

        # Verificar si ya está sanitizado
        if "sanitize_for_log" in linea:
            logs_sanitizados += 1
            continue

        # Verificar si contiene datos sensibles sin sanitizar
        for patron, descripcion in patrones_sensibles:
            if re.search(patron, linea, re.IGNORECASE):
                logs_sin_sanitizar.append(
                    {"linea": num_linea, "codigo": linea.strip(), "motivo": descripcion}
                )
                break

    return logs_sanitizados, logs_sin_sanitizar


if __name__ == "__main__":
    print("=" * 80)
    print("VERIFICACIÓN DE SANITIZACIÓN DE LOGS - ufe.py")
    print("=" * 80)
    print()

    logs_ok, logs_pendientes = verificar_sanitizacion()

    print(f"✅ Logs sanitizados correctamente: {logs_ok}")
    print(f"⚠️  Logs pendientes de sanitizar: {len(logs_pendientes)}")
    print()

    if logs_pendientes:
        print("📋 CASOS PENDIENTES DE SANITIZACIÓN:")
        print("=" * 80)
        for caso in logs_pendientes[:20]:  # Mostrar primeros 20
            print(f"\n  Línea {caso['linea']}: {caso['motivo']}")
            print(f"  {caso['codigo'][:100]}")  # Primeros 100 chars

        if len(logs_pendientes) > 20:
            print(f"\n  ... y {len(logs_pendientes) - 20} casos más")
    else:
        print("🎉 ¡TODOS LOS LOGS ESTÁN SANITIZADOS!")

    print()
    print("=" * 80)

    # Resumen de progreso
    total = logs_ok + len(logs_pendientes)
    porcentaje = (logs_ok / total * 100) if total > 0 else 0
    print(f"PROGRESO: {logs_ok}/{total} ({porcentaje:.1f}%)")
    print("=" * 80)
