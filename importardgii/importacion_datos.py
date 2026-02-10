# importacion_datos.py
# Importación de datos del archivo Excel a las tablas en SQL Server

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
from estructura_tablas import obtener_conexion_sql

def es_fecha_valida(valor):
    """
    Verifica si un valor es una fecha válida para SQL Server
    Args:
        valor: Valor a verificar
    Returns:
        bool: True si es una fecha válida, False en caso contrario
    """
    try:
        if isinstance(valor, datetime):
            # Verificar que esté dentro del rango permitido por SQL Server (1753-01-01 a 9999-12-31)
            min_date = datetime(1753, 1, 1)
            max_date = datetime(9999, 12, 31)
            return min_date <= valor <= max_date
        elif isinstance(valor, str):
            # Intentar convertir la cadena a fecha
            fecha = None
            # Patrones comunes de fechas
            patrones = [
                '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
                '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%m-%d-%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S'
            ]
            
            for patron in patrones:
                try:
                    fecha = datetime.strptime(valor, patron)
                    break
                except ValueError:
                    continue
            
            if fecha:
                min_date = datetime(1753, 1, 1)
                max_date = datetime(9999, 12, 31)
                return min_date <= fecha <= max_date
            
            return False
        else:
            return False
    except Exception:
        return False

def limpiar_valor_para_sql(valor, tipo_columna=None):
    """
    Limpia y formatea un valor para ser insertado en SQL Server
    
    Args:
        valor: Valor a limpiar
        tipo_columna: Tipo de columna en SQL Server (opcional)
    
    Returns:
        Valor limpio para SQL Server o None si debe ser NULL
    """
    # Si es NaN o None, devolver None
    if pd.isna(valor):
        return None
        
    # Si es un valor nulo específico (#e), devolver None
    if isinstance(valor, str) and valor.strip() == VALOR_NULO:
        return None
        
    # Si es una fecha
    if isinstance(valor, datetime) or (tipo_columna and 'datetime' in tipo_columna):
        try:
            if isinstance(valor, datetime):
                # Verificar si está dentro del rango válido
                if es_fecha_valida(valor):
                    return valor.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    print(f"Advertencia: Fecha fuera de rango - {valor}. Se establecerá como NULL.")
                    return None
            elif isinstance(valor, str):
                # Intentar convertir la cadena a fecha
                if es_fecha_valida(valor):
                    return valor
                else:
                    print(f"Advertencia: No se pudo convertir a fecha - '{valor}'. Se establecerá como NULL.")
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al procesar fecha - {valor}: {str(e)}. Se establecerá como NULL.")
            return None
    
    # Convertir cualquier valor a string para evitar problemas de tipo
    if not pd.isna(valor):
        if isinstance(valor, (int, float, bool)):
            return valor  # Mantener tipos numéricos y booleanos
        else:
            return str(valor)  # Convertir otros tipos a string
    
    return valor

def obtener_tipos_columnas(cursor, tabla):
    """
    Obtiene los tipos de datos de las columnas de una tabla
    
    Args:
        cursor: Cursor de conexión a SQL Server
        tabla: Nombre de la tabla
    
    Returns:
        dict: Diccionario con los nombres de columnas y sus tipos de datos
    """
    try:
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{tabla}'
        """)
        tipos_columnas = {}
        for row in cursor.fetchall():
            col_name, data_type, max_length = row
            # Para columnas nvarchar, agregar el tamaño máximo
            if data_type == 'nvarchar' and max_length is not None:
                tipos_columnas[col_name] = f"{data_type}({max_length})"
            else:
                tipos_columnas[col_name] = data_type
        return tipos_columnas
    except Exception as e:
        print(f"Error al obtener tipos de columnas para la tabla {tabla}: {str(e)}")
        return {}

# Modificación en importacion_datos.py
# Función modificada para garantizar que los campos problemáticos solo se asignen a la tabla Encabezado

# Modificación en importacion_datos.py
# Solución para el error de EncabezadoID

def importar_excel_a_sqlserver(ruta_archivo_excel=RUTA_ARCHIVO_EXCEL, 
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
    Importa datos de un archivo Excel a dos tablas en SQL Server: Encabezado y Detalle.
    """
    print(f"Iniciando importación del archivo: {ruta_archivo_excel}")
    
    # Leer el archivo Excel
    print(f"Leyendo archivo Excel (hoja {nombre_hoja})...")
    df = pd.read_excel(ruta_archivo_excel, sheet_name=nombre_hoja)
    
    # Obtener los encabezados
    headers = list(df.columns)
    
    # Encontrar los índices donde termina el encabezado y comienza el detalle
    idx_fin_encabezado = headers.index(columna_fin_encabezado) if columna_fin_encabezado in headers else -1
    idx_inicio_detalle = headers.index(columna_inicio_detalle) if columna_inicio_detalle in headers else -1
    
    if idx_fin_encabezado == -1 or idx_inicio_detalle == -1:
        raise ValueError(f"No se pudieron encontrar las columnas clave para separar encabezado y detalle.")
    
    print(f"Encabezado termina en columna {idx_fin_encabezado}: {headers[idx_fin_encabezado]}")
    print(f"Detalle comienza en columna {idx_inicio_detalle}: {headers[idx_inicio_detalle]}")
    
    # Identificar los bloques de detalle
    bloques_detalle = {}
    for col in headers:
        if '[' in col and ']' in col:
            try:
                nombre_base = col.split('[')[0]
                indice = int(col.split('[')[1].split(']')[0])
                
                if indice not in bloques_detalle:
                    bloques_detalle[indice] = []
                
                bloques_detalle[indice].append(col)
            except (ValueError, IndexError):
                # Ignorar columnas con formato [texto] que no sean índices numéricos
                continue
    
    # Verificar cuántos bloques de detalle hay
    if len(bloques_detalle) == 0:
        print("⚠ Advertencia: No se encontraron bloques de detalle con el formato Nombre[índice]")
    else:
        print(f"Se encontraron {len(bloques_detalle)} bloques de detalle (de [1] a [{max(bloques_detalle.keys())}])")
    
    # Identificar columnas de encabezado
    columnas_encabezado_pre = headers[:idx_inicio_detalle]
    
    # Identificar el final de todos los bloques de detalle
    if bloques_detalle:
        ultimo_indice = max(bloques_detalle.keys())
        ultima_columna_ultimo_bloque = "MontoItem[" + str(ultimo_indice) + "]"
        try:
            idx_fin_ultimo_detalle = headers.index(ultima_columna_ultimo_bloque)
            columnas_encabezado_post = headers[idx_fin_ultimo_detalle + 1:]
        except ValueError:
            print(f"⚠ Advertencia: No se encontró la columna {ultima_columna_ultimo_bloque}")
            columnas_encabezado_post = []
    else:
        columnas_encabezado_post = []
    
    # Todas las columnas de encabezado
    columnas_encabezado = columnas_encabezado_pre + columnas_encabezado_post
    
    try:
        print(f"Conectando a SQL Server ({servidor})...")
        conn = obtener_conexion_sql(servidor, base_datos, usuario, password, trusted_connection)
        cursor = conn.cursor()
        print("Conexión establecida con éxito")
        
        # Obtener las columnas válidas de la tabla Detalle
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FEDetalle'")
        columnas_detalle_validas = set(row[0] for row in cursor.fetchall())
        print(f"La tabla Detalle tiene {len(columnas_detalle_validas)} columnas válidas")
        
        # Obtener tipos de columnas
        tipos_columnas_encabezado = obtener_tipos_columnas(cursor, 'FEEncabezado')
        tipos_columnas_detalle = obtener_tipos_columnas(cursor, 'FEDetalle')
        
        # Procesar cada fila del Excel
        total_filas = len(df)
        print(f"Procesando {total_filas} filas del archivo Excel")
        
        for idx, row in df.iterrows():
            try:
                # Extraer datos del encabezado
                encabezado_data = {}
                
                # Procesar columnas de encabezado al inicio
                for col in columnas_encabezado_pre:
                    nombre_columna = col.replace('[', '').replace(']', '')
                    tipo_columna = tipos_columnas_encabezado.get(nombre_columna, '')
                    valor = limpiar_valor_para_sql(row[col], tipo_columna)
                    
                    encabezado_data[nombre_columna] = valor
                
                # Procesar columnas de encabezado al final
                for col in columnas_encabezado_post:
                    nombre_columna = col.replace('[', '').replace(']', '')
                    tipo_columna = tipos_columnas_encabezado.get(nombre_columna, '')
                    valor = limpiar_valor_para_sql(row[col], tipo_columna)
                    
                    encabezado_data[nombre_columna] = valor
                
                # Insertar en tabla Encabezado
                if encabezado_data:
                    encabezado_cols = ', '.join([f"[{col}]" for col in encabezado_data.keys()])
                    encabezado_placeholders = ', '.join(['?' for _ in encabezado_data])
                    encabezado_values = list(encabezado_data.values())
                    
                    sql_encabezado = f"INSERT INTO FEEncabezado ({encabezado_cols}) VALUES ({encabezado_placeholders})"
                    cursor.execute(sql_encabezado, encabezado_values)
                    
                    # Guardar valores necesarios para el detalle
                    ENCF = encabezado_data.get('ENCF')
                    RNCEmisor = encabezado_data.get('RNCEmisor')
                    TipoeCF = encabezado_data.get('TipoeCF')
                    
                    # Procesar los bloques de detalle
                    for indice in bloques_detalle:
                        # Verificar si este bloque tiene datos
                        tiene_datos = False
                        for col in bloques_detalle[indice]:
                            if not pd.isna(row[col]) and (not isinstance(row[col], str) or row[col].strip() != valor_nulo):
                                tiene_datos = True
                                break
                        
                        if not tiene_datos:
                            continue  # Saltar este bloque si no tiene datos
                        
                        # Preparar datos para esta línea de detalle
                        detalle_data = {}
                        
                        # Verificar si la columna NumeroLinea existe en la tabla Detalle
                        if 'NumeroLinea' in columnas_detalle_validas:
                            detalle_data['NumeroLinea'] = indice
                        
                        # Extraer valores para esta línea de detalle
                        for col in bloques_detalle[indice]:
                            # Quitar el índice del nombre
                            nombre_base = col.split('[')[0]
                            
                            # Verificar que la columna existe en la tabla Detalle antes de agregarla
                            if nombre_base in columnas_detalle_validas:
                                tipo_columna = tipos_columnas_detalle.get(nombre_base, '')
                                valor = limpiar_valor_para_sql(row[col], tipo_columna)
                                
                                
                                '''
                                # Si la columna es nvarchar, verificar longitud
                                if tipo_columna and 'nvarchar' in tipo_columna:
                                    try:
                                        # Extraer tamaño entre paréntesis
                                        tamano = int(tipo_columna.split('(')[1].split(')')[0])+1
                                        if valor and isinstance(valor, str) and len(valor) > tamano:
                                            print(f"⚠ Advertencia: Valor truncado para columna {nombre_base}. Original: '{valor[:20]}...' ({len(valor)} caracteres), máximo: {tamano}")
                                            valor = valor[:tamano]  # Truncar al tamaño máximo
                                    except (IndexError, ValueError):
                                        pass
                                '''
                                detalle_data[nombre_base] = valor
                        
                        # Agregar campos fijos del encabezado que también van en el detalle
                        # Solo si existen en la tabla Detalle
                        for campo, valor_campo in [
                            ('ENCF', ENCF),
                            ('RNCEmisor', RNCEmisor), 
                            ('TipoeCF', TipoeCF)
                        ]:
                            if campo in columnas_detalle_validas and valor_campo is not None:
                                detalle_data[campo] = valor_campo
                        
                        # Insertar en tabla Detalle solo si hay datos
                        if detalle_data:
                            detalle_cols = ', '.join([f"[{col}]" for col in detalle_data.keys()])
                            detalle_placeholders = ', '.join(['?' for _ in detalle_data])
                            detalle_values = list(detalle_data.values())
                            
                            sql_detalle = f"INSERT INTO FEDetalle ({detalle_cols}) VALUES ({detalle_placeholders})"
                            cursor.execute(sql_detalle, detalle_values)
                
                # Commit por cada registro procesado
                conn.commit()
                
                if (idx + 1) % 10 == 0 or (idx + 1) == total_filas:
                    print(f"Procesados {idx + 1} de {total_filas} registros")
                
            except Exception as e:
                print(f"Error procesando fila {idx + 1}: {str(e)}")
                traceback.print_exc()
                conn.rollback()
        
        print("Importación completada con éxito")
    
    except Exception as e:
        print(f"Error en la conexión o procesamiento: {str(e)}")
        traceback.print_exc()
        raise
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Conexión cerrada")
            
if __name__ == "__main__":
    importar_excel_a_sqlserver()