# importacion_soluciones.py
# Soluciones para el problema de importación de datos de fecha

import pandas as pd
import numpy as np
from datetime import datetime
import pyodbc
import traceback
from configuracion import (
    RUTA_ARCHIVO_EXCEL, SERVIDOR_SQL, BASE_DATOS_SQL, USUARIO_SQL, 
    PASSWORD_SQL, TRUSTED_CONNECTION, NOMBRE_HOJA, COLUMNA_FIN_ENCABEZADO, 
    COLUMNA_INICIO_DETALLE, NUMERO_MAXIMO_DETALLES, VALOR_NULO
)
from importardgii.estructura_tablas import obtener_conexion_sql

def diagnosticar_problema_fechas(ruta_archivo_excel=RUTA_ARCHIVO_EXCEL, 
                              servidor=SERVIDOR_SQL, 
                              base_datos=BASE_DATOS_SQL, 
                              usuario=USUARIO_SQL, 
                              password=PASSWORD_SQL, 
                              trusted_connection=TRUSTED_CONNECTION,
                              nombre_hoja=NOMBRE_HOJA,
                              columna_fin_encabezado=COLUMNA_FIN_ENCABEZADO,
                              columna_inicio_detalle=COLUMNA_INICIO_DETALLE):
    """
    Diagnostica problemas de fechas en la importación de datos.
    
    Args:
        [Parámetros de configuración]
    
    Returns:
        tuple: (tiene_problemas, columnas_problematicas)
    """
    print(f"Iniciando diagnóstico de problemas de fechas: {ruta_archivo_excel}")
    
    # Leer el archivo Excel
    print(f"Leyendo archivo Excel (hoja {nombre_hoja})...")
    df = pd.read_excel(ruta_archivo_excel, sheet_name=nombre_hoja)
    
    # Obtener los encabezados
    headers = list(df.columns)
    
    # Encontrar los índices donde termina el encabezado y comienza el detalle
    idx_fin_encabezado = headers.index(columna_fin_encabezado) if columna_fin_encabezado in headers else -1
    idx_inicio_detalle = headers.index(columna_inicio_detalle) if columna_inicio_detalle in headers else -1
    
    if idx_fin_encabezado == -1 or idx_inicio_detalle == -1:
        raise ValueError(f"No se pudieron encontrar las columnas clave.")
    
    tiene_problemas = False
    columnas_problematicas = []
    
    try:
        conn = obtener_conexion_sql(servidor, base_datos, usuario, password, trusted_connection)
        cursor = conn.cursor()
        
        # Obtener columnas de tipo datetime
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Encabezado' AND DATA_TYPE = 'datetime'
        """)
        columnas_datetime = [row[0] for row in cursor.fetchall()]
        
        print(f"Se encontraron {len(columnas_datetime)} columnas de tipo datetime en la tabla Encabezado:")
        for col in columnas_datetime:
            print(f"  - {col}")
        
        # Analizar la primera fila para buscar valores problemáticos
        if len(df) > 0 and columnas_datetime:
            print("\nAnalizando los datos para detectar posibles problemas de fecha...")
            problemas_encontrados = []
            
            for i, row in df.iterrows():
                for col_datetime in columnas_datetime:
                    # Buscar la columna correspondiente en el Excel
                    col_excel = next((c for c in headers if c.replace('[', '_').replace(']', '') == col_datetime), None)
                    
                    if col_excel and col_excel in headers[:idx_fin_encabezado + 1]:
                        valor = row[col_excel]
                        
                        if pd.isna(valor) or (isinstance(valor, str) and valor.strip() == VALOR_NULO):
                            # Valores nulos no causan problemas
                            pass
                        elif isinstance(valor, datetime):
                            min_date = datetime(1753, 1, 1)
                            max_date = datetime(9999, 12, 31)
                            if not (min_date <= valor <= max_date):
                                problemas_encontrados.append((col_datetime, valor, i+1))
                                if col_datetime not in columnas_problematicas:
                                    columnas_problematicas.append(col_datetime)
                        else:
                            problemas_encontrados.append((col_datetime, valor, i+1))
                            if col_datetime not in columnas_problematicas:
                                columnas_problematicas.append(col_datetime)
            
            if problemas_encontrados:
                tiene_problemas = True
                print("\n⚠ Se encontraron problemas con campos de fecha:")
                for columna, valor, fila in problemas_encontrados[:10]:  # Mostrar solo los primeros 10
                    print(f"  - Fila {fila}, Columna: '{columna}', Valor: '{valor}', Tipo: {type(valor)}")
                
                if len(problemas_encontrados) > 10:
                    print(f"  ... y {len(problemas_encontrados) - 10} problemas más.")
            else:
                print("✓ No se encontraron problemas evidentes con los campos de fecha")
        
    except Exception as e:
        print(f"Error en el diagnóstico: {str(e)}")
        traceback.print_exc()
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    
    return tiene_problemas, columnas_problematicas

def convertir_columnas_datetime_a_nvarchar(columnas=None, 
                                          servidor=SERVIDOR_SQL, 
                                          base_datos=BASE_DATOS_SQL, 
                                          usuario=USUARIO_SQL, 
                                          password=PASSWORD_SQL, 
                                          trusted_connection=TRUSTED_CONNECTION,
                                          confirmar=True):
    """
    Convierte columnas de tipo datetime a nvarchar(50) en la tabla Encabezado
    
    Args:
        columnas: Lista de columnas a convertir (None = todas las columnas datetime)
        servidor: Nombre del servidor SQL Server
        base_datos: Nombre de la base de datos
        usuario: Nombre de usuario SQL Server
        password: Contraseña SQL Server
        trusted_connection: Usar autenticación Windows
        confirmar: Si es True, pide confirmación antes de ejecutar

    Returns:
        bool: True si la conversión fue exitosa, False en caso contrario
    """
    try:
        print("Conectando a SQL Server para convertir columnas...")
        conn = obtener_conexion_sql(servidor, base_datos, usuario, password, trusted_connection)
        cursor = conn.cursor()
        
        # Si no se especificaron columnas, obtener todas las de tipo datetime
        if columnas is None:
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Encabezado' AND DATA_TYPE = 'datetime'
            """)
            columnas_datetime = [row[0] for row in cursor.fetchall()]
        else:
            columnas_datetime = columnas
        
        if not columnas_datetime:
            print("No se encontraron columnas de tipo datetime para convertir.")
            return True
        
        print(f"Se van a convertir {len(columnas_datetime)} columnas de tipo datetime a nvarchar(50):")
        for col in columnas_datetime:
            print(f"  - {col}")
        
        # Confirmar si se desea continuar
        if confirmar:
            confirmar_input = input("¿Desea convertir estas columnas a nvarchar(50)? (s/n): ")
            if confirmar_input.lower() not in ['s', 'si', 'y', 'yes']:
                print("Operación cancelada.")
                return False
        
        columnas_convertidas = []
        columnas_error = []
        
        # Convertir cada columna
        for columna in columnas_datetime:
            try:
                print(f"Convirtiendo columna {columna}...")
                
                # Crear columna temporal
                sql_temp = f"ALTER TABLE Encabezado ADD [Temp_{columna}] nvarchar(50) NULL"
                cursor.execute(sql_temp)
                
                # Copiar datos
                sql_copy = f"UPDATE Encabezado SET [Temp_{columna}] = CONVERT(nvarchar(50), [{columna}], 121)"
                cursor.execute(sql_copy)
                
                # Eliminar columna original
                sql_drop = f"ALTER TABLE Encabezado DROP COLUMN [{columna}]"
                cursor.execute(sql_drop)
                
                # Renombrar columna temporal
                sql_rename = f"EXEC sp_rename 'Encabezado.Temp_{columna}', '{columna}', 'COLUMN'"
                cursor.execute(sql_rename)
                
                print(f"✓ Columna {columna} convertida exitosamente")
                columnas_convertidas.append(columna)
                
                # Commit por cada columna
                conn.commit()
                
            except Exception as e:
                print(f"Error al convertir columna {columna}: {str(e)}")
                columnas_error.append(columna)
                conn.rollback()
        
        if columnas_convertidas and not columnas_error:
            print(f"✓ Conversión completada con éxito. Se convirtieron {len(columnas_convertidas)} columnas.")
            return True
        elif columnas_convertidas and columnas_error:
            print(f"⚠ Conversión parcial. Se convirtieron {len(columnas_convertidas)} columnas, pero hubo errores en {len(columnas_error)} columnas.")
            return False
        else:
            print("⚠ No se pudo convertir ninguna columna.")
            return False
    
    except Exception as e:
        print(f"Error al conectar o ejecutar consultas: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Conexión cerrada")

def importar_como_texto(ruta_archivo_excel=RUTA_ARCHIVO_EXCEL, 
                       servidor=SERVIDOR_SQL, 
                       base_datos=BASE_DATOS_SQL, 
                       usuario=USUARIO_SQL, 
                       password=PASSWORD_SQL, 
                       trusted_connection=TRUSTED_CONNECTION,
                       nombre_hoja=NOMBRE_HOJA,
                       columna_fin_encabezado=COLUMNA_FIN_ENCABEZADO,
                       columna_inicio_detalle=COLUMNA_INICIO_DETALLE,
                       numero_maximo_detalles=NUMERO_MAXIMO_DETALLES,
                       valor_nulo=VALOR_NULO):
    """
    Importa todos los datos como texto, sin conversión de tipos
    
    Args:
        [Mismos argumentos que importar_excel_a_sqlserver]
        
    Returns:
        bool: True si la importación fue exitosa, False en caso contrario
    """
    print(f"Iniciando importación como texto: {ruta_archivo_excel}")
    
    # Leer el archivo Excel
    print(f"Leyendo archivo Excel (hoja {nombre_hoja})...")
    df = pd.read_excel(ruta_archivo_excel, sheet_name=nombre_hoja)
    
    # Procesar el DataFrame
    # Obtener los encabezados
    headers = list(df.columns)
    
    # Encontrar los índices donde termina el encabezado y comienza el detalle
    idx_fin_encabezado = headers.index(columna_fin_encabezado) if columna_fin_encabezado in headers else -1
    idx_inicio_detalle = headers.index(columna_inicio_detalle) if columna_inicio_detalle in headers else -1
    
    if idx_fin_encabezado == -1 or idx_inicio_detalle == -1:
        raise ValueError(f"No se pudieron encontrar las columnas clave para separar encabezado y detalle.")
    
    print(f"Encabezado termina en columna {idx_fin_encabezado}: {headers[idx_fin_encabezado]}")
    print(f"Detalle comienza en columna {idx_inicio_detalle}: {headers[idx_inicio_detalle]}")
    
    registros_exitosos = 0
    registros_error = 0
    errores = []
    
    # Crear conexión a la base de datos
    try:
        print(f"Conectando a SQL Server ({servidor})...")
        conn = obtener_conexion_sql(servidor, base_datos, usuario, password, trusted_connection)
        cursor = conn.cursor()
        print("Conexión establecida con éxito")
        
        # Procesar cada fila del Excel
        total_filas = len(df)
        print(f"Procesando {total_filas} filas del archivo Excel")
        
        for idx, row in df.iterrows():
            try:
                # Extraer datos del encabezado (columnas 0 a idx_fin_encabezado)
                encabezado_data = {}
                for i in range(0, idx_fin_encabezado + 1):
                    nombre_columna = headers[i].replace('[', '_').replace(']', '')
                    valor = row[headers[i]]
                    
                    # Convertir todos los valores a string para evitar problemas de tipo
                    if pd.isna(valor):
                        valor = None  # NULL en SQL
                    elif isinstance(valor, str) and valor.strip() == valor_nulo:
                        valor = None  # NULL en SQL
                    elif isinstance(valor, datetime):
                        # Convertir fecha a string en formato ISO
                        valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # Convertir cualquier otro valor a string
                        valor = str(valor) if valor is not None else None
                    
                    encabezado_data[nombre_columna] = valor
                
                # Insertar en tabla Encabezado
                if encabezado_data:
                    encabezado_cols = ', '.join([f"[{col}]" for col in encabezado_data.keys()])
                    encabezado_placeholders = ', '.join(['?' for _ in encabezado_data])
                    encabezado_values = list(encabezado_data.values())
                    
                    sql_encabezado = f"INSERT INTO Encabezado ({encabezado_cols}) VALUES ({encabezado_placeholders})"
                    
                    try:
                        cursor.execute(sql_encabezado, encabezado_values)
                        
                        # Obtener ID de encabezado recién insertado
                        cursor.execute("SELECT SCOPE_IDENTITY()")
                        encabezado_id = cursor.fetchone()[0]
                        
                        # Procesar los detalles
                        detalles_procesados = 0
                        
                        for linea in range(1, numero_maximo_detalles + 1):
                            detalle_data = {'EncabezadoID': encabezado_id}  # Relacionar con el encabezado
                            
                            # Para cada línea de detalle, obtener todos los campos correspondientes
                            campos_detalle = [col for col in headers if f"[{linea}]" in col]
                            
                            # Solo procesar si hay datos en el detalle (verificar al menos una columna no vacía)
                            tiene_datos = False
                            for campo in campos_detalle:
                                if not pd.isna(row[campo]) and (not isinstance(row[campo], str) or row[campo].strip() != valor_nulo):
                                    tiene_datos = True
                                    break
                            
                            if not tiene_datos:
                                continue  # Saltar esta línea de detalle si no tiene datos
                            
                            # Extraer valores para esta línea de detalle
                            for campo in campos_detalle:
                                nombre_campo = campo.replace(f"[{linea}]", "")  # Quitar el índice del nombre
                                valor = row[campo]
                                
                                # Convertir todos los valores a string
                                if pd.isna(valor):
                                    valor = None  # NULL en SQL
                                elif isinstance(valor, str) and valor.strip() == valor_nulo:
                                    valor = None  # NULL en SQL
                                elif isinstance(valor, datetime):
                                    valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    valor = str(valor) if valor is not None else None
                                
                                detalle_data[nombre_campo] = valor
                            
                            # Insertar en tabla Detalle
                            if len(detalle_data) > 1:  # Si solo tiene EncabezadoID, no hay datos reales
                                detalle_cols = ', '.join([f"[{col}]" for col in detalle_data.keys()])
                                detalle_placeholders = ', '.join(['?' for _ in detalle_data])
                                detalle_values = list(detalle_data.values())
                                
                                sql_detalle = f"INSERT INTO Detalle ({detalle_cols}) VALUES ({detalle_placeholders})"
                                cursor.execute(sql_detalle, detalle_values)
                                detalles_procesados += 1
                        
                        # Commit por cada registro procesado
                        conn.commit()
                        registros_exitosos += 1
                        
                        # Mostrar progreso
                        if (idx + 1) % 10 == 0 or (idx + 1) == total_filas:
                            print(f"Procesados {idx + 1} de {total_filas} registros")
                    
                    except Exception as e:
                        error_msg = f"Error al insertar fila {idx + 1}: {str(e)}"
                        print(error_msg)
                        errores.append(error_msg)
                        registros_error += 1
                        conn.rollback()
                
            except Exception as e:
                error_msg = f"Error procesando fila {idx + 1}: {str(e)}"
                print(error_msg)
                errores.append(error_msg)
                registros_error += 1
                conn.rollback()
        
        print(f"\nImportación completada:")
        print(f"- Registros exitosos: {registros_exitosos}")
        print(f"- Registros con error: {registros_error}")
        
        if registros_exitosos > 0 and registros_error == 0:
            print("✓ Importación exitosa al 100%")
            return True
        elif registros_exitosos > 0 and registros_error > 0:
            print("⚠ Importación parcial")
            return False
        else:
            print("⚠ La importación falló completamente")
            return False
    
    except Exception as e:
        print(f"Error en la conexión o procesamiento: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Conexión cerrada")

def solucion_automatica_fechas(ruta_archivo_excel=RUTA_ARCHIVO_EXCEL, 
                              servidor=SERVIDOR_SQL, 
                              base_datos=BASE_DATOS_SQL, 
                              usuario=USUARIO_SQL, 
                              password=PASSWORD_SQL, 
                              trusted_connection=TRUSTED_CONNECTION,
                              nombre_hoja=NOMBRE_HOJA,
                              columna_fin_encabezado=COLUMNA_FIN_ENCABEZADO,
                              columna_inicio_detalle=COLUMNA_INICIO_DETALLE,
                              numero_maximo_detalles=NUMERO_MAXIMO_DETALLES,
                              valor_nulo=VALOR_NULO,
                              modo_interactivo=True):
    """
    Solución automática para problemas de fecha en la importación
    
    Args:
        [Mismos argumentos que importar_excel_a_sqlserver]
        modo_interactivo: Si es True, solicita confirmación al usuario
        
    Returns:
        bool: True si la importación fue exitosa, False en caso contrario
    """
    print("Iniciando solución automática para problemas de fecha...\n")
    
    # Paso 1: Diagnosticar el problema
    print("Paso 1: Diagnóstico del problema")
    print("--------------------------------")
    tiene_problemas, columnas_problematicas = diagnosticar_problema_fechas(
        ruta_archivo_excel, servidor, base_datos, usuario, password, 
        trusted_connection, nombre_hoja, columna_fin_encabezado, columna_inicio_detalle
    )
    
    if not tiene_problemas:
        print("\n✓ No se detectaron problemas de fecha. Puede proceder con la importación normal.")
        return True
    
    # Paso 2: Convertir columnas
    print("\nPaso 2: Conversión de columnas")
    print("----------------------------")
    print("Se procederá a convertir las columnas problemáticas a formato texto (nvarchar).")
    
    if modo_interactivo:
        confirmar = input("¿Desea continuar con la conversión? (s/n): ")
        if confirmar.lower() not in ['s', 'si', 'y', 'yes']:
            print("Operación cancelada.")
            return False
    
    conversion_exitosa = convertir_columnas_datetime_a_nvarchar(
        columnas_problematicas, servidor, base_datos, usuario, 
        password, trusted_connection, confirmar=False
    )
    
    if not conversion_exitosa:
        print("\n⚠ Hubo problemas en la conversión de columnas. Se recomienda revisar manualmente.")
        if modo_interactivo:
            continuar = input("¿Desea intentar la importación de todas formas? (s/n): ")
            if continuar.lower() not in ['s', 'si', 'y', 'yes']:
                print("Operación cancelada.")
                return False
    
    # Paso 3: Importar datos como texto
    print("\nPaso 3: Importación de datos")
    print("--------------------------")
    print("Se procederá a importar los datos tratando todos los valores como texto.")
    
    if modo_interactivo:
        confirmar = input("¿Desea continuar con la importación? (s/n): ")
        if confirmar.lower() not in ['s', 'si', 'y', 'yes']:
            print("Operación cancelada.")
            return False
    
    importacion_exitosa = importar_como_texto(
        ruta_archivo_excel, servidor, base_datos, usuario, password, 
        trusted_connection, nombre_hoja, columna_fin_encabezado, 
        columna_inicio_detalle, numero_maximo_detalles, valor_nulo
    )
    
    if importacion_exitosa:
        print("\n✓ Proceso completado con éxito!")
        return True
    else:
        print("\n⚠ La importación presentó algunos problemas.")
        return False

if __name__ == "__main__":
    solucion_automatica_fechas()