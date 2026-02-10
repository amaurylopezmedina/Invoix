# estructura_tablas.py
# Gestión de la estructura de tablas en SQL Server

import pyodbc
import traceback
from configuracion import SERVIDOR_SQL, BASE_DATOS_SQL, USUARIO_SQL, PASSWORD_SQL, TRUSTED_CONNECTION

def obtener_conexion_sql(servidor=SERVIDOR_SQL, base_datos=BASE_DATOS_SQL, 
                         usuario=USUARIO_SQL, password=PASSWORD_SQL, 
                         trusted_connection=TRUSTED_CONNECTION):
    """
    Establece y devuelve una conexión a SQL Server.
    
    Args:
        servidor (str): Nombre del servidor SQL Server
        base_datos (str): Nombre de la base de datos
        usuario (str, opcional): Nombre de usuario para SQL Server
        password (str, opcional): Contraseña para SQL Server
        trusted_connection (bool, opcional): Si es True, usa la autenticación de Windows
        
    Returns:
        pyodbc.Connection: Objeto de conexión a SQL Server
    """
    try:
        if trusted_connection:
            conn_str = f'DRIVER={{SQL Server}};SERVER={servidor};DATABASE={base_datos};Trusted_Connection=yes;'
        else:
            conn_str = f'DRIVER={{SQL Server}};SERVER={servidor};DATABASE={base_datos};UID={usuario};PWD={password}'
        
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error al conectar con SQL Server: {str(e)}")
        raise

def verificar_columnas_encabezado(cursor, columnas_requeridas):
    """
    Verifica si todas las columnas requeridas existen en la tabla Encabezado.
    Si faltan columnas, las añade a la tabla.
    
    Args:
        cursor: Cursor de conexión a SQL Server
        columnas_requeridas: Lista de tuplas con (nombre_columna, tipo_de_dato)
        
    Returns:
        bool: True si la tabla existe, False si no existe
    """
    # Comprobar si la tabla Encabezado existe
    cursor.execute("IF OBJECT_ID('FEEncabezado', 'U') IS NOT NULL SELECT 1 ELSE SELECT 0")
    tabla_existe = cursor.fetchone()[0]
    
    if not tabla_existe:
        print("La tabla Encabezado no existe. Se creará con todas las columnas necesarias.")
        return False
    
    # Si la tabla existe, obtener las columnas actuales
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Encabezado'")
    columnas_actuales = [row[0] for row in cursor.fetchall()]
    
    # Verificar qué columnas faltan
    columnas_faltantes = []
    for nombre_col, tipo_col in columnas_requeridas:
        if nombre_col not in columnas_actuales:
            columnas_faltantes.append((nombre_col, tipo_col))
    
    # Si faltan columnas, agregarlas
    if columnas_faltantes:
        print(f"Se encontraron {len(columnas_faltantes)} columnas faltantes en la tabla Encabezado. Agregando...")
        for nombre_col, tipo_col in columnas_faltantes:
            try:
                cursor.execute(f"ALTER TABLE FEEncabezado ADD [{nombre_col}] {tipo_col} NULL")
                print(f"Columna agregada: {nombre_col}")
            except Exception as e:
                print(f"Error al agregar columna {nombre_col}: {str(e)}")
    else:
        print("La tabla Encabezado ya tiene todas las columnas necesarias.")
    
    return True

def verificar_tabla_detalle(cursor):
    """
    Verifica si la tabla Detalle existe. Si no existe, la crea con todas las columnas necesarias.
    Si existe, verifica que tenga todas las columnas requeridas y las añade si faltan.
    
    Args:
        cursor: Cursor de conexión a SQL Server
        
    Returns:
        bool: True si la tabla existe, False si no existe
    """
    # Definir todas las columnas que debe tener la tabla Detalle
    columnas_detalle = [
        ("DetalleID", "int", "IDENTITY(1,1) PRIMARY KEY"),
        ("EncabezadoID", "int", "FOREIGN KEY REFERENCES [dbo].[FEEncabezado]([EncabezadoID])"),
        ("NumeroLinea", "int", "NULL"),
        ("TipoCodigo1", "nvarchar(50)", "NULL"),
        ("CodigoItem1", "nvarchar(50)", "NULL"),
        ("TipoCodigo2", "nvarchar(50)", "NULL"),
        ("CodigoItem2", "nvarchar(50)", "NULL"),
        ("TipoCodigo3", "nvarchar(50)", "NULL"),
        ("CodigoItem3", "nvarchar(50)", "NULL"),
        ("TipoCodigo4", "nvarchar(50)", "NULL"),
        ("CodigoItem4", "nvarchar(50)", "NULL"),
        ("TipoCodigo5", "nvarchar(50)", "NULL"),
        ("CodigoItem5", "nvarchar(50)", "NULL"),
        ("IndicadorFacturacion", "nvarchar(50)", "NULL"),
        ("IndicadorAgenteRetencionoPercepcion", "nvarchar(50)", "NULL"),
        ("MontoITBISRetenido", "decimal(18, 2)", "NULL"),
        ("MontoISRRetenido", "decimal(18, 2)", "NULL"),
        ("NombreItem", "nvarchar(80)", "NULL"),
        ("IndicadorBienoServicio", "nvarchar(50)", "NULL"),
        ("DescripcionItem", "nvarchar(1100)", "NULL"),
        ("CantidadItem", "decimal(18, 2)", "NULL"),
        ("UnidadMedida", "nvarchar(50)", "NULL"),
        ("CantidadReferencia", "decimal(18, 2)", "NULL"),
        ("UnidadReferencia", "nvarchar(50)", "NULL"),
        ("Subcantidad", "decimal(18, 2)", "NULL"),
        ("CodigoSubcantidad", "nvarchar(50)", "NULL"),
        ("GradosAlcohol", "decimal(18, 2)", "NULL"),
        ("PrecioUnitarioReferencia", "decimal(18, 2)", "NULL"),
        ("FechaElaboracion", "datetime", "NULL"),
        ("FechaVencimientoItem", "datetime", "NULL"),
        ("PesoNetoKilogramo", "decimal(18, 2)", "NULL"),
        ("PesoNetoMineria", "decimal(18, 2)", "NULL"),
        ("TipoAfiliacion", "nvarchar(50)", "NULL"),
        ("Liquidacion", "nvarchar(50)", "NULL"),
        ("PrecioUnitarioItem", "decimal(18, 2)", "NULL"),
        ("DescuentoMonto", "decimal(18, 2)", "NULL"),
        ("TipoSubDescuento", "nvarchar(50)", "NULL"),
        ("SubDescuentoPorcentaje", "decimal(18, 2)", "NULL"),
        ("MontoSubDescuento", "decimal(18, 2)", "NULL"),
        ("RecargoMonto", "decimal(18, 2)", "NULL"),
        ("TipoSubRecargo", "nvarchar(50)", "NULL"),
        ("SubRecargoPorcentaje", "decimal(18, 2)", "NULL"),
        ("MontosubRecargo", "decimal(18, 2)", "NULL"),
        ("TipoImpuesto", "nvarchar(50)", "NULL"),
        ("PrecioOtraMoneda", "decimal(18, 2)", "NULL"),
        ("DescuentoOtraMoneda", "decimal(18, 2)", "NULL"),
        ("RecargoOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoItemOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoItem", "decimal(18, 2)", "NULL"),
        
        # Columnas faltantes según el error
        ("FormaPago", "nvarchar(50)", "NULL"),
        ("MontoPago", "decimal(18, 2)", "NULL"),
        ("TelefonoEmisor", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicional", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecifico", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvalorem", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionales", "decimal(18, 2)", "NULL"),
        ("TipoImpuestoOtraMoneda", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicionalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesOtraMoneda", "decimal(18, 2)", "NULL"),
        
        # Líneas de descuento o recargo
        ("NumeroLineaDoR", "int", "NULL"),
        ("TipoAjuste", "nvarchar(50)", "NULL"),
        ("IndicadorNorma1007", "nvarchar(50)", "NULL"),
        ("DescripcionDescuentooRecargo", "nvarchar(255)", "NULL"),
        ("TipoValor", "nvarchar(50)", "NULL"),
        ("ValorDescuentooRecargo", "decimal(18, 2)", "NULL"),
        ("MontoDescuentooRecargo", "decimal(18, 2)", "NULL"),
        ("MontoDescuentooRecargoOtraMoneda", "decimal(18, 2)", "NULL"),
        ("IndicadorFacturacionDescuentooRecargo", "nvarchar(50)", "NULL"),
        
        # Totales página
        ("PaginaNo", "int", "NULL"),
        ("NoLineaDesde", "int", "NULL"),
        ("NoLineaHasta", "int", "NULL"),
        ("SubtotalMontoGravadoPagina", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado1Pagina", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado2Pagina", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado3Pagina", "decimal(18, 2)", "NULL"),
        ("SubtotalExentoPagina", "decimal(18, 2)", "NULL"),
        ("SubtotalItbisPagina", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis1Pagina", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis2Pagina", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis3Pagina", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoAdicionalPagina", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoAdicionalPaginaTabla", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoSelectivoConsumoEspecificoPagina", "decimal(18, 2)", "NULL"),
        ("SubtotalOtrosImpuesto", "decimal(18, 2)", "NULL"),
        ("MontoSubtotalPagina", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoNoFacturablePagina", "decimal(18, 2)", "NULL")
    ]
    
    # Comprobar si la tabla Detalle existe
    cursor.execute("IF OBJECT_ID('FEDetalle', 'U') IS NOT NULL SELECT 1 ELSE SELECT 0")
    tabla_existe = cursor.fetchone()[0]
    
    if not tabla_existe:
        print("La tabla Detalle no existe. Se creará...")
        # SQL para crear tabla Detalle
        sql_crear_detalle = "CREATE TABLE [dbo].[FEDetalle] (\n"
        
        # Agregar todas las columnas
        for i, (nombre_col, tipo_col, nullable) in enumerate(columnas_detalle):
            if i > 0:
                sql_crear_detalle += ",\n"
            sql_crear_detalle += f"[{nombre_col}] {tipo_col} {nullable}"
        
        sql_crear_detalle += "\n)"
        
        cursor.execute(sql_crear_detalle)
        print("Tabla Detalle creada exitosamente.")
        return False
    else:
        print("La tabla Detalle ya existe. Verificando columnas...")
        
        # Obtener columnas actuales
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FEDetalle'")
        columnas_actuales = [row[0] for row in cursor.fetchall()]
        
        # Verificar qué columnas faltan
        columnas_faltantes = []
        for nombre_col, tipo_col, nullable in columnas_detalle:
            if nombre_col not in columnas_actuales:
                columnas_faltantes.append((nombre_col, tipo_col, nullable))
        
        # Si faltan columnas, agregarlas
        if columnas_faltantes:
            print(f"Se encontraron {len(columnas_faltantes)} columnas faltantes en la tabla Detalle. Agregando...")
            for nombre_col, tipo_col, nullable in columnas_faltantes:
                try:
                    cursor.execute(f"ALTER TABLE FEDetalle ADD [{nombre_col}] {tipo_col} {nullable}")
                    print(f"Columna agregada a Detalle: {nombre_col}")
                except Exception as e:
                    print(f"Error al agregar columna {nombre_col} a Detalle: {str(e)}")
        else:
            print("La tabla Detalle ya tiene todas las columnas necesarias.")
        
        return True
    
def crear_o_actualizar_tablas(servidor=SERVIDOR_SQL, base_datos=BASE_DATOS_SQL, 
                            usuario=USUARIO_SQL, password=PASSWORD_SQL, 
                            trusted_connection=TRUSTED_CONNECTION):
    """
    Verifica y actualiza la estructura de las tablas en SQL Server.
    
    Args:
        servidor (str): Nombre del servidor SQL Server
        base_datos (str): Nombre de la base de datos
        usuario (str, opcional): Nombre de usuario para SQL Server
        password (str, opcional): Contraseña para SQL Server
        trusted_connection (bool, opcional): Si es True, usa la autenticación de Windows
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    # Definir columnas requeridas (nombre, tipo_de_dato)
    columnas_requeridas = [
        # Columnas básicas
        ("CasoPrueba", "nvarchar(255)"),
        ("Version", "nvarchar(50)"),
        ("TipoeCF", "nvarchar(50)"),
        ("ENCF", "nvarchar(100)"),
        ("FechaVencimientoSecuencia", "nvarchar(50)"),
        ("IndicadorNotaCredito", "nvarchar(50)"),
        ("IndicadorEnvioDiferido", "nvarchar(50)"),
        ("IndicadorMontoGravado", "nvarchar(50)"),
        ("TipoIngresos", "nvarchar(50)"),
        ("TipoPago", "nvarchar(50)"),
        ("FechaLimitePago", "nvarchar(50)"),
        ("TerminoPago", "nvarchar(100)"),
        
        # Formas de pago
        ("FormaPago1", "nvarchar(50)"),
        ("MontoPago1", "decimal(18, 2)"),
        ("FormaPago2", "nvarchar(50)"),
        ("MontoPago2", "decimal(18, 2)"),
        ("FormaPago3", "nvarchar(50)"),
        ("MontoPago3", "decimal(18, 2)"),
        ("FormaPago4", "nvarchar(50)"),
        ("MontoPago4", "decimal(18, 2)"),
        ("FormaPago5", "nvarchar(50)"),
        ("MontoPago5", "decimal(18, 2)"),
        ("FormaPago6", "nvarchar(50)"),
        ("MontoPago6", "decimal(18, 2)"),
        ("FormaPago7", "nvarchar(50)"),
        ("MontoPago7", "decimal(18, 2)"),
        
        # Datos del emisor
        ("RNCEmisor", "nvarchar(50)"),
        ("RazonSocialEmisor", "nvarchar(255)"),
        ("NombreComercialEmisor", "nvarchar(255)"),
        ("TipoSucursal", "nvarchar(50)"),
        ("CodigoSucursal", "nvarchar(50)"),
        ("DireccionEmisor", "nvarchar(255)"),
        ("TelefonoEmisor1", "nvarchar(50)"),
        ("TelefonoEmisor2", "nvarchar(50)"),
        ("TelefonoEmisor3", "nvarchar(50)"),
        ("CorreoEmisor", "nvarchar(255)"),
        ("WebSiteEmisor", "nvarchar(255)"),
        ("ActividadEconomicaEmisor", "nvarchar(255)"),
        ("CodigoVendedor", "nvarchar(255)"),
        ("NombreVendedor", "nvarchar(255)"),
        ("ResponsablePago", "nvarchar(255)"),
        
        # Datos del comprador
        ("TipoAceptacion", "nvarchar(50)"),
        ("RNCComprador", "nvarchar(50)"),
        ("IdentificacionExtranjeroComprador", "nvarchar(50)"),
        ("RazonSocialComprador", "nvarchar(255)"),
        ("ContactoComprador", "nvarchar(255)"),
        ("CorreoComprador", "nvarchar(255)"),
        ("DireccionComprador", "nvarchar(255)"),
        ("TelefonoComprador", "nvarchar(50)"),
        
        # Impuestos
        ("TablaImpuestoAdicional", "nvarchar(50)"),
        ("TipoImpuesto", "nvarchar(50)"),
        ("TasaImpuestoAdicional", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecifico", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvalorem", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionales", "decimal(18, 2)"),
        ("TipoImpuesto1", "nvarchar(50)"),
        ("TasaImpuestoAdicional1", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecifico1", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvalorem1", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionales1", "decimal(18, 2)"),
        ("TipoImpuesto2", "nvarchar(50)"),
        ("TasaImpuestoAdicional2", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecifico2", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvalorem2", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionales2", "decimal(18, 2)"),
        ("TipoImpuesto3", "nvarchar(50)"),
        ("TasaImpuestoAdicional3", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecifico3", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvalorem3", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionales3", "decimal(18, 2)"),
        ("TipoImpuesto4", "nvarchar(50)"),
        ("TasaImpuestoAdicional4", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecifico4", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvalorem4", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionales4", "decimal(18, 2)"),
        
        # Fechas
        ("FechaEmision", "nvarchar(50)"),
        ("FechaEmisionDocumentoModificado", "nvarchar(50)"),
        ("Fecha", "nvarchar(50)"),
        ("FechaInicio", "nvarchar(50)"),
        ("FechaTermino", "nvarchar(50)"),
        ("FechaValidez", "nvarchar(50)"),
        
        # Indicadores
        ("IndicadorServicioTipoBienesCompras", "nvarchar(50)"),
        ("IndicadorMedioPago", "nvarchar(50)"),
        ("IndicadorServicioTipoBienesCompras2", "nvarchar(50)"),
        ("IndicadorM", "nvarchar(50)"),
        ("CondicionComprobante", "nvarchar(50)"),
        
        # Documento modificado
        ("TipoDocumentoModificado", "nvarchar(50)"),
        ("RNCEmisorDocumentoModificado", "nvarchar(50)"),
        ("NumeroDocumentoModificado", "nvarchar(50)"),
        ("NumeroComprobanteFiscalModificado", "nvarchar(50)"),
        
        # Otros impuestos
        ("RNCOtroImpuesto", "nvarchar(50)"),
        ("CodigoOtroImpuesto", "nvarchar(50)"),
        ("IndicadorFacturacion", "nvarchar(50)"),
        ("IndicadorAgenteRetencionoPercepcion", "nvarchar(50)"),
        ("MontoITBISRetenido", "decimal(18, 2)"),
        ("MontoISRRetenido", "decimal(18, 2)"),
        ("IndicadorNorma1007", "nvarchar(50)"),
        ("InformacionAdicional", "nvarchar(max)"),
        
        # Montos generales
        ("MontoGravadoTotal", "decimal(18, 2)"),
        ("MontoGravado1", "decimal(18, 2)"),
        ("MontoGravado2", "decimal(18, 2)"),
        ("MontoGravado3", "decimal(18, 2)"),
        ("MontoExento", "decimal(18, 2)"),
        ("MontoItbisTotal", "decimal(18, 2)"),
        ("MontoItbis1", "decimal(18, 2)"),
        ("MontoItbis2", "decimal(18, 2)"),
        ("MontoItbis3", "decimal(18, 2)"),
        ("MontoImpuestoAdicional", "decimal(18, 2)"),
        ("MontoImpuestoAdicionalTabla", "decimal(18, 2)"),
        ("MontoImpuestosAdicionalTotal", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecificoTotal", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvaloremTotal", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionalesTotal", "decimal(18, 2)"),
        ("MontoTotal", "decimal(18, 2)"),
        ("MontoNoFacturable", "decimal(18, 2)"),
        ("MontoPeriodo", "decimal(18, 2)"),
        ("SaldoAnterior", "decimal(18, 2)"),
        ("MontoAvancePago", "decimal(18, 2)"),
        ("ValorPagar", "decimal(18, 2)"),
# Más datos sobre el comprobante
        ("TipoeCFModificado", "nvarchar(50)"),
        ("IndicadorDocumentoReferencia", "nvarchar(50)"),
        ("TipoRetencionPercepcion", "nvarchar(50)"),
        ("MontoRetencionPercepcion", "decimal(18, 2)"),
        ("FechaRetencionPercepcion", "nvarchar(50)"),
        ("DetallePago", "nvarchar(max)"),
        ("TipoSujetoRetenido", "nvarchar(50)"),
        ("TipoPagoRetencion", "nvarchar(50)"),
        ("FechaPagoRetenido", "nvarchar(50)"),
        ("MontoSujetoaRetencion", "decimal(18, 2)"),
        
        # Datos bancarios
        ("TipoCuentaTercero", "nvarchar(50)"),
        ("NumeroCuentaTercero", "nvarchar(50)"),
        ("NombrePropietarioCuenta", "nvarchar(255)"),
        ("DocumentoIdentidadPropietario", "nvarchar(50)"),
        ("NombreBanco", "nvarchar(255)"),
        ("NumeroCheque", "nvarchar(50)"),
        
        # Montos por método de pago
        ("MontoEfectivo", "decimal(18, 2)"),
        ("MontoCheque", "decimal(18, 2)"),
        ("MontoAbono", "decimal(18, 2)"),
        ("MontoDebito", "decimal(18, 2)"),
        ("MontoCredito", "decimal(18, 2)"),
        
        # Montos en otra moneda
        ("TipoMonedaOtraMoneda", "nvarchar(50)"),
        ("TasaCambioOtraMoneda", "decimal(18, 2)"),
        ("MontoGravadoTotalOtraMoneda", "decimal(18, 2)"),
        ("MontoGravado1OtraMoneda", "decimal(18, 2)"),
        ("MontoGravado2OtraMoneda", "decimal(18, 2)"),
        ("MontoGravado3OtraMoneda", "decimal(18, 2)"),
        ("MontoExentoOtraMoneda", "decimal(18, 2)"),
        ("MontoItbisTotalOtraMoneda", "decimal(18, 2)"),
        ("MontoItbis1OtraMoneda", "decimal(18, 2)"),
        ("MontoItbis2OtraMoneda", "decimal(18, 2)"),
        ("MontoItbis3OtraMoneda", "decimal(18, 2)"),
        ("MontoImpuestoAdicionalOtraMoneda", "decimal(18, 2)"),
        ("MontoImpuestoAdicionalTablaOtraMoneda", "decimal(18, 2)"),
        
        # Impuestos en otra moneda
        ("TipoImpuestoOtraMoneda1", "nvarchar(50)"),
        ("TasaImpuestoAdicionalOtraMoneda1", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda1", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda1", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionalesOtraMoneda1", "decimal(18, 2)"),
        ("TipoImpuestoOtraMoneda2", "nvarchar(50)"),
        ("TasaImpuestoAdicionalOtraMoneda2", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda2", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda2", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionalesOtraMoneda2", "decimal(18, 2)"),
        ("TipoImpuestoOtraMoneda3", "nvarchar(50)"),
        ("TasaImpuestoAdicionalOtraMoneda3", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda3", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda3", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionalesOtraMoneda3", "decimal(18, 2)"),
        ("TipoImpuestoOtraMoneda4", "nvarchar(50)"),
        ("TasaImpuestoAdicionalOtraMoneda4", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda4", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda4", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionalesOtraMoneda4", "decimal(18, 2)"),
        ("MontoImpuestosAdicionalTotalOtraMoneda", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoEspecificoTotalOtraMoneda", "decimal(18, 2)"),
        ("MontoImpuestoSelectivoConsumoAdvaloremTotalOtraMoneda", "decimal(18, 2)"),
        ("OtrosImpuestosAdicionalesOtraMonedaTotal", "decimal(18, 2)"),
        ("MontoTotalOtraMoneda", "decimal(18, 2)"),
        
        # Columnas adicionales que aparecieron en el error
        ("TipoCuentaPago", "nvarchar(50)"),
        ("NumeroCuentaPago", "nvarchar(100)"),
        ("BancoPago", "nvarchar(100)"),
        ("FechaDesde", "nvarchar(50)"),
        ("FechaHasta", "nvarchar(50)"),
        ("TotalPaginas", "int"),
        ("NombreComercial", "nvarchar(255)"),
        ("Sucursal", "nvarchar(100)"),
        ("Municipio", "nvarchar(100)"),
        ("Provincia", "nvarchar(100)"),
        ("WebSite", "nvarchar(255)"),
        ("ActividadEconomica", "nvarchar(255)"),
        ("NumeroFacturaInterna", "nvarchar(100)"),
        ("NumeroPedidoInterno", "nvarchar(100)"),
        ("ZonaVenta", "nvarchar(100)"),
        ("RutaVenta", "nvarchar(100)"),
        ("InformacionAdicionalEmisor", "nvarchar(max)"),
        ("IdentificadorExtranjero", "nvarchar(100)"),
        ("MunicipioComprador", "nvarchar(100)"),
        ("ProvinciaComprador", "nvarchar(100)"),
        ("PaisComprador", "nvarchar(100)"),
        ("FechaEntrega", "nvarchar(50)"),
        ("ContactoEntrega", "nvarchar(255)"),
        ("DireccionEntrega", "nvarchar(255)"),
        ("TelefonoAdicional", "nvarchar(50)"),
        ("FechaOrdenCompra", "nvarchar(50)"),
        ("NumeroOrdenCompra", "nvarchar(100)"),
        ("CodigoInternoComprador", "nvarchar(100)"),
        ("InformacionAdicionalComprador", "nvarchar(max)"),
        ("FechaEmbarque", "nvarchar(50)"),
        ("NumeroEmbarque", "nvarchar(100)"),
        ("NumeroContenedor", "nvarchar(100)"),
        ("NumeroReferencia", "nvarchar(100)"),
        ("NombrePuertoEmbarque", "nvarchar(255)"),
        ("CondicionesEntrega", "nvarchar(255)"),
        ("TotalFob", "decimal(18, 2)"),
        ("Seguro", "decimal(18, 2)"),
        ("Flete", "decimal(18, 2)"),
        ("OtrosGastos", "decimal(18, 2)"),
        ("TotalCif", "decimal(18, 2)"),
        ("RegimenAduanero", "nvarchar(100)"),
        ("NombrePuertoSalida", "nvarchar(255)"),
        ("NombrePuertoDesembarque", "nvarchar(255)"),
        ("PesoBruto", "decimal(18, 2)"),
        ("PesoNeto", "decimal(18, 2)"),
        ("UnidadPesoBruto", "nvarchar(50)"),
        ("UnidadPesoNeto", "nvarchar(50)"),
        ("CantidadBulto", "decimal(18, 2)"),
        ("UnidadBulto", "nvarchar(50)"),
        ("VolumenBulto", "decimal(18, 2)"),
        ("UnidadVolumen", "nvarchar(50)"),
        ("ViaTransporte", "nvarchar(100)"),
        ("PaisOrigen", "nvarchar(100)"),
        ("DireccionDestino", "nvarchar(255)"),
        ("PaisDestino", "nvarchar(100)"),
        ("RNCIdentificacionCompaniaTransportista", "nvarchar(100)"),
        ("NombreCompaniaTransportista", "nvarchar(255)"),
        ("NumeroViaje", "nvarchar(100)"),
        ("Conductor", "nvarchar(255)"),
        ("DocumentoTransporte", "nvarchar(100)"),
        ("Ficha", "nvarchar(100)"),
        ("Placa", "nvarchar(100)"),
        ("RutaTransporte", "nvarchar(100)"),
        ("ZonaTransporte", "nvarchar(100)"),
        ("NumeroAlbaran", "nvarchar(100)"),
        ("MontoGravadoI1", "decimal(18, 2)"),
        ("MontoGravadoI2", "decimal(18, 2)"),
        ("MontoGravadoI3", "decimal(18, 2)"),
        ("ITBIS1", "decimal(18, 2)"),
        ("ITBIS2", "decimal(18, 2)"),
        ("ITBIS3", "decimal(18, 2)"),
        ("TotalITBIS", "decimal(18, 2)"),
        ("TotalITBIS1", "decimal(18, 2)"),
        ("TotalITBIS2", "decimal(18, 2)"),
        ("TotalITBIS3", "decimal(18, 2)"),
        ("TotalITBISRetenido", "decimal(18, 2)"),
        ("TotalISRRetencion", "decimal(18, 2)"),
        ("TotalITBISPercepcion", "decimal(18, 2)"),
        ("TotalISRPercepcion", "decimal(18, 2)"),
        ("TipoMoneda", "nvarchar(50)"),
        ("TipoCambio", "decimal(18, 6)"),
        ("TotalITBISOtraMoneda", "decimal(18, 2)"),
        ("TotalITBIS1OtraMoneda", "decimal(18, 2)"),
        ("TotalITBIS2OtraMoneda", "decimal(18, 2)"),
        ("TotalITBIS3OtraMoneda", "decimal(18, 2)"),
        

        
        # Columnas faltantes según el error
        ("DescripcionSubtotal", "nvarchar(255)"),
        ("Orden", "int"),
        ("SubTotalMontoGravadoTotal", "decimal(18, 2)"),
        ("SubTotalMontoGravadoI1", "decimal(18, 2)"),
        ("SubTotalMontoGravadoI2", "decimal(18, 2)"),
        ("SubTotalMontoGravadoI3", "decimal(18, 2)"),
        ("SubTotaITBIS", "decimal(18, 2)"),
        ("SubTotaITBIS1", "decimal(18, 2)"),
        ("SubTotaITBIS2", "decimal(18, 2)"),
        ("SubTotaITBIS3", "decimal(18, 2)"),
        ("SubTotalImpuestoAdicional", "decimal(18, 2)"),
        ("MontoSubTotal", "decimal(18, 2)"),
        ("Lineas", "int"),
        
        # Líneas de descuento o recargo 1
        ("NumeroLineaDoR1", "int"),
        ("TipoAjuste1", "nvarchar(50)"),
        ("IndicadorNorma10071", "nvarchar(50)"),
        ("DescripcionDescuentooRecargo1", "nvarchar(255)"),
        ("TipoValor1", "nvarchar(50)"),
        ("ValorDescuentooRecargo1", "decimal(18, 2)"),
        ("MontoDescuentooRecargo1", "decimal(18, 2)"),
        ("MontoDescuentooRecargoOtraMoneda1", "decimal(18, 2)"),
        ("IndicadorFacturacionDescuentooRecargo1", "nvarchar(50)"),
        
        # Líneas de descuento o recargo 2
        ("NumeroLineaDoR2", "int"),
        ("TipoAjuste2", "nvarchar(50)"),
        ("IndicadorNorma10072", "nvarchar(50)"),
        ("DescripcionDescuentooRecargo2", "nvarchar(255)"),
        ("TipoValor2", "nvarchar(50)"),
        ("ValorDescuentooRecargo2", "decimal(18, 2)"),
        ("MontoDescuentooRecargo2", "decimal(18, 2)"),
        ("MontoDescuentooRecargoOtraMoneda2", "decimal(18, 2)"),
        ("IndicadorFacturacionDescuentooRecargo2", "nvarchar(50)"),
        
        # Totales página 1
        ("PaginaNo1", "int"),
        ("NoLineaDesde1", "int"),
        ("NoLineaHasta1", "int"),
        ("SubtotalMontoGravadoPagina1", "decimal(18, 2)"),
        ("SubtotalMontoGravado1Pagina1", "decimal(18, 2)"),
        ("SubtotalMontoGravado2Pagina1", "decimal(18, 2)"),
        ("SubtotalMontoGravado3Pagina1", "decimal(18, 2)"),
        ("SubtotalExentoPagina1", "decimal(18, 2)"),
        ("SubtotalItbisPagina1", "decimal(18, 2)"),
        ("SubtotalItbis1Pagina1", "decimal(18, 2)"),
        ("SubtotalItbis2Pagina1", "decimal(18, 2)"),
        ("SubtotalItbis3Pagina1", "decimal(18, 2)"),
        ("SubtotalImpuestoAdicionalPagina1", "decimal(18, 2)"),
        ("SubtotalImpuestoAdicionalPaginaTabla1", "decimal(18, 2)"),
        ("SubtotalImpuestoSelectivoConsumoEspecificoPagina11", "decimal(18, 2)"),
        ("SubtotalOtrosImpuesto11", "decimal(18, 2)"),
        ("MontoSubtotalPagina1", "decimal(18, 2)"),
        ("SubtotalMontoNoFacturablePagina1", "decimal(18, 2)"),
        
        # Totales página 2
        ("PaginaNo2", "int"),
        ("NoLineaDesde2", "int"),
        ("NoLineaHasta2", "int"),
        ("SubtotalMontoGravadoPagina2", "decimal(18, 2)"),
        ("SubtotalMontoGravado1Pagina2", "decimal(18, 2)"),
        ("SubtotalMontoGravado2Pagina2", "decimal(18, 2)"),
        ("SubtotalMontoGravado3Pagina2", "decimal(18, 2)"),
        ("SubtotalExentoPagina2", "decimal(18, 2)"),
        ("SubtotalItbisPagina2", "decimal(18, 2)"),
        ("SubtotalItbis1Pagina2", "decimal(18, 2)"),
        ("SubtotalItbis2Pagina2", "decimal(18, 2)"),
        ("SubtotalItbis3Pagina2", "decimal(18, 2)"),
        ("SubtotalImpuestoAdicionalPagina2", "decimal(18, 2)"),
        ("SubtotalImpuestoSelectivoConsumoEspecificoPagina21", "decimal(18, 2)"),
        ("SubtotalOtrosImpuesto21", "decimal(18, 2)"),
        ("MontoSubtotalPagina2", "decimal(18, 2)"),
        ("SubtotalMontoNoFacturablePagina2", "decimal(18, 2)"),
        
        # Campos de modificación
        ("NCFModificado", "nvarchar(100)"),
        ("RNCOtroContribuyente", "nvarchar(50)"),
        ("FechaNCFModificado", "nvarchar(50)"),
        ("CodigoModificacion", "nvarchar(50)"),
        ("ConteoImpresiones", "int", "default 0"),
        ("ResultadoEstadoFiscal", "varchar(max)", "NULL"),
        ("MontoDGII", "numeric(18,4)", "NULL"), 
        ("MontoITBISDGII", "numeric(18,4)", "NULL"),
        ("EstadoFiscal", "int", "DEFAULT 1"),
        ("Estadoimpresion", "int", "DEFAULT 1"),
        ("URLQR", "char(255)", "NULL"),
        ("fechacreacion", "DATETIME", "DEFAULT GETDATE()"),
        ("CodigoSeguridad", "char(100)", "NULL"),
        ("CodigoSeguridadCF", "char(10)", "NULL"),
        ("Trackid", "char(255)", "NULL"),
        ("FechaFirma", "char(50)", "NULL")
        
    ]
    
    try:
            print("Conectando a SQL Server para verificar tablas...")
            conn = obtener_conexion_sql(servidor, base_datos, usuario, password, trusted_connection)
            cursor = conn.cursor()
            
            # Verificar si la tabla Encabezado existe y tiene las columnas necesarias
            tabla_encabezado_existe = verificar_columnas_encabezado(cursor, columnas_requeridas)
            
            # Si la tabla Encabezado no existe, la creamos
            if not tabla_encabezado_existe:
                # SQL para crear tabla Encabezado
                sql_crear_encabezado = """
                CREATE TABLE [dbo].[FEEncabezado] (
                    [EncabezadoID] [int] IDENTITY(1,1) PRIMARY KEY
                """
                
                # Agregar todas las columnas
                for nombre_col, tipo_col in columnas_requeridas:
                    sql_crear_encabezado += f",\n[{nombre_col}] {tipo_col} NULL"
                    sql_crear_encabezado += f",\n[{nombre_col}] {tipo_col} NULL"
                
                sql_crear_encabezado += "\n)"
                
                cursor.execute(sql_crear_encabezado)
                print("Tabla Encabezado creada exitosamente.")
            
            # Verificar si la tabla Detalle existe
            verificar_tabla_detalle(cursor)
            
            conn.commit()
            print("Verificación y actualización de tablas completada con éxito")
            return True
            
    except Exception as e:
        print(f"Error al verificar o actualizar tablas: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    crear_o_actualizar_tablas()