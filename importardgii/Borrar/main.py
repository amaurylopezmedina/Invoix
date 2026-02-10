# main.py
# Script principal para importar datos de Excel a SQL Server

import os
import sys
from configuracion import *
from crear_ambas_tablas import *
from importardgii.estructura_tablas import crear_o_actualizar_tablas
from importacion_datos import importar_excel_a_sqlserver
from importacion_soluciones import (
    diagnosticar_problema_fechas,
    convertir_columnas_datetime_a_nvarchar,
    importar_como_texto,
    solucion_automatica_fechas
)
from config_loader import load_config, update_config_variables


def procesar_argumentos():
    
    config = load_config()
    
    # Parámetros por defecto (tomados de la configuración JSON)
    parametros = {
        'ruta_archivo': config["RUTA_ARCHIVO_EXCEL"],
        'servidor': config["SERVIDOR_SQL"],
        'base_datos': config["BASE_DATOS_SQL"],
        'usuario': config["USUARIO_SQL"],
        'password': config["PASSWORD_SQL"],
        'trusted_connection': config["TRUSTED_CONNECTION"],
        'solo_estructura': False,
        'solo_importacion': False,
        'diagnostico': False,
        'convertir_fechas': False,
        'importar_texto': False,
        'solucion_fechas': False,
        'modo_interactivo': True,
        'configurar': False
    }
    

    
    return parametros

def main():
    """Función principal."""
    print("Iniciando proceso de importación de Excel a SQL Server")
    
    # Procesar argumentos de línea de comandos
    parametros = procesar_argumentos()
    
    # Verificar si el archivo Excel existe
    if not os.path.exists(parametros['ruta_archivo']) and not parametros['solo_estructura']:
        print(f"ERROR: El archivo Excel {parametros['ruta_archivo']} no existe.")
        return 1

    
    # Importar datos
    print("\n2. Importando datos desde Excel...")
    try:
        
        crear_ambas_tablas(
            parametros['servidor'],
            parametros['base_datos'],
            parametros['usuario'],
            parametros['password'],
            parametros['trusted_connection']
        )
                
        importar_excel_a_sqlserver(
            ruta_archivo_excel=parametros['ruta_archivo'],
            servidor=parametros['servidor'],
            base_datos=parametros['base_datos'],
            usuario=parametros['usuario'],
            password=parametros['password'],
            trusted_connection=parametros['trusted_connection']
        )
    except Exception as e:
        # Si es otro tipo de error, simplemente mostrar el mensaje
        print(f"\nERROR: {str(e)}")
        return 1
        
    print("\nProceso completado exitosamente.")
    return 0

if __name__ == "__main__":
    sys.exit(main())