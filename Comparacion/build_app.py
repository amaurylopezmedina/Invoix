# Script de construcción optimizado para app3.py
# Uso: python build_app.py

import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build():
    """Limpia directorios de construcción anteriores"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Eliminado directorio: {dir_name}")

    # Limpiar archivos .spec antiguos si existen
    for file in Path(".").glob("*.spec"):
        if file.name != "app3.spec":
            file.unlink()
            print(f"✓ Eliminado archivo spec antiguo: {file.name}")


def check_dependencies():
    """Verifica que PyInstaller esté instalado"""
    try:
        import PyInstaller

        print(f"✓ PyInstaller versión: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller no está instalado")
        print("Instalar con: pip install pyinstaller")
        return False


def build_app():
    """Construye la aplicación usando PyInstaller"""
    print("🏗️  Construyendo aplicación...")

    # Comando de construcción optimizado
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",  # Limpiar cache
        "--noconfirm",  # No pedir confirmación
        "app3.spec",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

        if result.returncode == 0:
            print("✓ Construcción exitosa")
            print("✓ Ejecutable creado en: dist/app3.exe")

            # Mostrar tamaño del ejecutable
            exe_path = Path("dist/app3.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✓ Tamaño del ejecutable: {size_mb:.2f} MB")
            return True
        else:
            print("✗ Error en la construcción:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"✗ Error ejecutando PyInstaller: {e}")
        return False


def create_portable_version():
    """Crea una versión portable con configuración incluida"""
    print("📦 Creando versión portable...")

    dist_dir = Path("dist")
    portable_dir = Path("app3_portable")

    if not dist_dir.exists():
        print("✗ No existe directorio dist")
        return False

    # Crear directorio portable
    if portable_dir.exists():
        shutil.rmtree(portable_dir)

    portable_dir.mkdir()

    # Copiar ejecutable
    exe_src = dist_dir / "app3.exe"
    exe_dst = portable_dir / "app3.exe"

    if exe_src.exists():
        shutil.copy2(exe_src, exe_dst)
        print("✓ Ejecutable copiado")
    else:
        print("✗ Ejecutable no encontrado")
        return False

    # Copiar archivos de configuración si existen
    config_files = ["config.ini", "app3.log"]
    for config_file in config_files:
        if Path(config_file).exists():
            shutil.copy2(config_file, portable_dir / config_file)
            print(f"✓ Archivo de configuración copiado: {config_file}")

    # Crear archivo README portable
    readme_content = """# Sistema NCF - Versión Portable

Esta es una versión portable del Sistema NCF optimizado para comparación de datos.

## Requisitos
- Windows 10/11
- Conexión a base de datos SQL Server (configurar en config.ini)

## Configuración
1. Editar config.ini con los datos de conexión a la base de datos
2. Ejecutar app3.exe

## Notas
- Los archivos de configuración se guardan en el mismo directorio
- Los logs se escriben en app3.log
"""

    (portable_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print("✓ README creado")

    # Crear archivo ZIP
    zip_name = f"app3_v2.0.0_portable"
    shutil.make_archive(zip_name, "zip", portable_dir)
    print(f"✓ Archivo ZIP creado: {zip_name}.zip")

    return True


def main():
    """Función principal"""
    print("🚀 Iniciando construcción de app3.py")
    print("=" * 50)

    # Verificar dependencias
    if not check_dependencies():
        return 1

    # Limpiar
    clean_build()

    # Construir
    if not build_app():
        return 1

    # Crear versión portable
    if not create_portable_version():
        return 1

    print("=" * 50)
    print("✅ Construcción completada exitosamente")
    print("📁 Archivos generados:")
    print("   - dist/app3.exe (ejecutable principal)")
    print("   - app3_v2.0.0_portable.zip (versión portable)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
