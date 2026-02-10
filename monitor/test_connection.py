#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a la base de datos
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(__file__))

from database import get_db_connection
from api_monitor import test_database_connection

if __name__ == "__main__":
    print("=== Prueba de Conexión a Base de Datos ===")
    print()
    
    try:
        print("1. Probando conexión...")
        result = test_database_connection()
        print(f"   Resultado: {result}")
        print()
        
        if "Conectado correctamente" in result:
            print("2. Probando consulta de prueba...")
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Probar una consulta simple a la vista vMonitorSentences
            cursor.execute("SELECT TOP 1 * FROM vMonitorSentences")
            columns = [column[0] for column in cursor.description]
            print(f"   Columnas disponibles: {', '.join(columns)}")
            
            cursor.close()
            conn.close()
            print("   ✅ Consulta exitosa!")
        else:
            print("❌ No se pudo conectar a la base de datos")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()