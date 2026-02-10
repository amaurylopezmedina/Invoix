import os
import sys
import json
import shutil
import win32serviceutil
import win32service
import subprocess
from pathlib import Path

def create_default_config():
    """Crea un archivo de configuración JSON por defecto"""
    config = {
        "executables": [
            {
                "path": "C:\\ruta\\a\\tu\\aplicacion1.exe",
                "description": "Descripción de la aplicación 1"
            },
            {
                "path": "C:\\ruta\\a\\tu\\aplicacion2.exe",
                "description": "Descripción de la aplicación 2"
            }
        ]
    }
    
    config_dir = "C:\\ProgramData\\ExecutableMonitor"
    os.makedirs(config_dir, exist_ok=True)
    
    with open(os.path.join(config_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=4)
    
    print(f"Archivo de configuración creado en {os.path.join(config_dir, 'config.json')}")

def install_dependencies():
    """Instala las dependencias necesarias"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32", "psutil"])
        print("Dependencias instaladas correctamente")
    except Exception as e:
        print(f"Error al instalar dependencias: {str(e)}")
        return False
    return True

def install_service():
    """Instala el servicio de Windows"""
    try:
        # Copiar el script del servicio al directorio de instalación
        service_script = os.path.abspath("ExecutableMonitorService.py")
        install_dir = "C:\\ProgramData\\ExecutableMonitor"
        os.makedirs(install_dir, exist_ok=True)
        
        shutil.copy2(service_script, os.path.join(install_dir, "ExecutableMonitorService.py"))
        
        # Instalar el servicio
        os.chdir(install_dir)
        subprocess.check_call([sys.executable, "ExecutableMonitorService.py", "install"])
        
        # Iniciar el servicio
        win32serviceutil.StartService("ExecutableMonitor")
        print("Servicio instalado e iniciado correctamente")
    except Exception as e:
        print(f"Error al instalar el servicio: {str(e)}")
        return False
    return True

def main():
    print("=== Instalador del Servicio Monitor de Ejecutables ===")
    
    # Instalar dependencias
    print("\nInstalando dependencias...")
    if not install_dependencies():
        print("No se pudieron instalar las dependencias. Abortando.")
        return
    
    # Crear configuración por defecto
    print("\nCreando archivo de configuración por defecto...")
    create_default_config()
    
    # Preguntar si desea editar la configuración
    edit_config = input("\n¿Desea editar el archivo de configuración ahora? (s/n): ").lower() == 's'
    if edit_config:
        config_path = "C:\\ProgramData\\ExecutableMonitor\\config.json"
        os.system(f"notepad {config_path}")
    
    # Instalar el servicio
    print("\nInstalando el servicio...")
    if install_service():
        print("\nInstalación completada con éxito.")
        print("El servicio 'ExecutableMonitor' ha sido instalado y está en ejecución.")
        print("Puede administrar el servicio desde el administrador de servicios de Windows.")
    else:
        print("\nLa instalación del servicio falló.")

if __name__ == "__main__":
    main()
