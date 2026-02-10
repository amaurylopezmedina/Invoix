# crear_ambas_tablas.py
# Script para crear tanto la tabla Encabezado como la tabla Detalle desde cero

import pyodbc
import traceback
from configuracion import SERVIDOR_SQL, BASE_DATOS_SQL, USUARIO_SQL, PASSWORD_SQL, TRUSTED_CONNECTION

def obtener_conexion_sql(servidor=SERVIDOR_SQL, base_datos=BASE_DATOS_SQL, 
                         usuario=USUARIO_SQL, password=PASSWORD_SQL, 
                         trusted_connection=TRUSTED_CONNECTION):
    """
    Establece y devuelve una conexión a SQL Server.
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

def crear_ambas_tablas(servidor=SERVIDOR_SQL, base_datos=BASE_DATOS_SQL, 
                      usuario=USUARIO_SQL, password=PASSWORD_SQL, 
                      trusted_connection=TRUSTED_CONNECTION):
    """
    Crea ambas tablas: Encabezado y Detalle
    """
    # Definir columnas de la tabla Encabezado
    columnas_encabezado = [
        ("EncabezadoID", "int", "IDENTITY(1,1) PRIMARY KEY"),
        ("CasoPrueba", "nvarchar(255)", "NULL"),
        ("Version", "nvarchar(50)", "NULL"),
        ("TipoeCF", "nvarchar(50)", "NULL"),
        ("ENCF", "nvarchar(100)", "NULL"),
        ("FechaVencimientoSecuencia", "nvarchar(50)", "NULL"),
        ("IndicadorNotaCredito", "nvarchar(50)", "NULL"),
        ("IndicadorEnvioDiferido", "nvarchar(50)", "NULL"),
        ("IndicadorMontoGravado", "nvarchar(50)", "NULL"),
        ("TipoIngresos", "nvarchar(50)", "NULL"),
        ("TipoPago", "nvarchar(50)", "NULL"),
        ("FechaLimitePago", "nvarchar(50)", "NULL"),
        ("TerminoPago", "nvarchar(100)", "NULL"),
        ("FormaPago1", "nvarchar(50)", "NULL"),
        ("MontoPago1", "decimal(18, 2)", "NULL"),
        ("FormaPago2", "nvarchar(50)", "NULL"),
        ("MontoPago2", "decimal(18, 2)", "NULL"),
        ("FormaPago3", "nvarchar(50)", "NULL"),
        ("MontoPago3", "decimal(18, 2)", "NULL"),
        ("FormaPago4", "nvarchar(50)", "NULL"),
        ("MontoPago4", "decimal(18, 2)", "NULL"),
        ("FormaPago5", "nvarchar(50)", "NULL"),
        ("MontoPago5", "decimal(18, 2)", "NULL"),
        ("FormaPago6", "nvarchar(50)", "NULL"),
        ("MontoPago6", "decimal(18, 2)", "NULL"),
        ("FormaPago7", "nvarchar(50)", "NULL"),
        ("MontoPago7", "decimal(18, 2)", "NULL"),
        ("RNCEmisor", "nvarchar(50)", "NULL"),
        ("RazonSocialEmisor", "nvarchar(255)", "NULL"),
        ("NombreComercialEmisor", "nvarchar(255)", "NULL"),
        ("TipoSucursal", "nvarchar(50)", "NULL"),
        ("CodigoSucursal", "nvarchar(50)", "NULL"),
        ("DireccionEmisor", "nvarchar(255)", "NULL"),
        ("TelefonoEmisor1", "nvarchar(50)", "NULL"),
        ("TelefonoEmisor2", "nvarchar(50)", "NULL"),
        ("TelefonoEmisor3", "nvarchar(50)", "NULL"),
        ("CorreoEmisor", "nvarchar(255)", "NULL"),
        ("WebSiteEmisor", "nvarchar(255)", "NULL"),
        ("ActividadEconomicaEmisor", "nvarchar(255)", "NULL"),
        ("CodigoVendedor", "nvarchar(255)", "NULL"),
        ("NombreVendedor", "nvarchar(255)", "NULL"),
        ("ResponsablePago", "nvarchar(255)", "NULL"),
        ("TipoAceptacion", "nvarchar(50)", "NULL"),
        ("RNCComprador", "nvarchar(50)", "NULL"),
        ("IdentificacionExtranjeroComprador", "nvarchar(50)", "NULL"),
        ("RazonSocialComprador", "nvarchar(255)", "NULL"),
        ("ContactoComprador", "nvarchar(255)", "NULL"),
        ("CorreoComprador", "nvarchar(255)", "NULL"),
        ("DireccionComprador", "nvarchar(255)", "NULL"),
        ("TelefonoComprador", "nvarchar(50)", "NULL"),
        ("TablaImpuestoAdicional", "nvarchar(50)", "NULL"),
        ("TipoImpuesto", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicional", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecifico", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvalorem", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionales", "decimal(18, 2)", "NULL"),
        ("TipoImpuesto1", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicional1", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecifico1", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvalorem1", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionales1", "decimal(18, 2)", "NULL"),
        ("TipoImpuesto2", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicional2", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecifico2", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvalorem2", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionales2", "decimal(18, 2)", "NULL"),
        ("TipoImpuesto3", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicional3", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecifico3", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvalorem3", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionales3", "decimal(18, 2)", "NULL"),
        ("TipoImpuesto4", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicional4", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecifico4", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvalorem4", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionales4", "decimal(18, 2)", "NULL"),
        ("FechaEmision", "nvarchar(50)", "NULL"),
        ("FechaEmisionDocumentoModificado", "nvarchar(50)", "NULL"),
        ("Fecha", "nvarchar(50)", "NULL"),
        ("FechaInicio", "nvarchar(50)", "NULL"),
        ("FechaTermino", "nvarchar(50)", "NULL"),
        ("FechaValidez", "nvarchar(50)", "NULL"),
        ("IndicadorServicioTipoBienesCompras", "nvarchar(50)", "NULL"),
        ("IndicadorMedioPago", "nvarchar(50)", "NULL"),
        ("IndicadorServicioTipoBienesCompras2", "nvarchar(50)", "NULL"),
        ("IndicadorM", "nvarchar(50)", "NULL"),
        ("CondicionComprobante", "nvarchar(50)", "NULL"),
        ("TipoDocumentoModificado", "nvarchar(50)", "NULL"),
        ("RNCEmisorDocumentoModificado", "nvarchar(50)", "NULL"),
        ("NumeroDocumentoModificado", "nvarchar(50)", "NULL"),
        ("NumeroComprobanteFiscalModificado", "nvarchar(50)", "NULL"),
        ("RNCOtroImpuesto", "nvarchar(50)", "NULL"),
        ("CodigoOtroImpuesto", "nvarchar(50)", "NULL"),
        ("IndicadorFacturacion", "nvarchar(50)", "NULL"),
        ("IndicadorAgenteRetencionoPercepcion", "nvarchar(50)", "NULL"),
        ("MontoITBISRetenido", "decimal(18, 2)", "NULL"),
        ("MontoISRRetenido", "decimal(18, 2)", "NULL"),
        ("IndicadorNorma1007", "nvarchar(50)", "NULL"),
        ("InformacionAdicional", "nvarchar(max)", "NULL"),
        ("MontoGravadoTotal", "decimal(18, 2)", "NULL"),
        ("MontoGravado1", "decimal(18, 2)", "NULL"),
        ("MontoGravado2", "decimal(18, 2)", "NULL"),
        ("MontoGravado3", "decimal(18, 2)", "NULL"),
        ("MontoExento", "decimal(18, 2)", "NULL"),
        ("MontoItbisTotal", "decimal(18, 2)", "NULL"),
        ("MontoItbis1", "decimal(18, 2)", "NULL"),
        ("MontoItbis2", "decimal(18, 2)", "NULL"),
        ("MontoItbis3", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoAdicional", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoAdicionalTabla", "decimal(18, 2)", "NULL"),
        ("MontoImpuestosAdicionalTotal", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoTotal", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremTotal", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesTotal", "decimal(18, 2)", "NULL"),
        ("MontoTotal", "decimal(18, 2)", "NULL"),
        ("MontoNoFacturable", "decimal(18, 2)", "NULL"),
        ("MontoPeriodo", "decimal(18, 2)", "NULL"),
        ("SaldoAnterior", "decimal(18, 2)", "NULL"),
        ("MontoAvancePago", "decimal(18, 2)", "NULL"),
        ("ValorPagar", "decimal(18, 2)", "NULL"),
        ("TipoeCFModificado", "nvarchar(50)", "NULL"),
        ("IndicadorDocumentoReferencia", "nvarchar(50)", "NULL"),
        ("TipoRetencionPercepcion", "nvarchar(50)", "NULL"),
        ("MontoRetencionPercepcion", "decimal(18, 2)", "NULL"),
        ("FechaRetencionPercepcion", "nvarchar(50)", "NULL"),
        ("DetallePago", "nvarchar(max)", "NULL"),
        ("TipoSujetoRetenido", "nvarchar(50)", "NULL"),
        ("TipoPagoRetencion", "nvarchar(50)", "NULL"),
        ("FechaPagoRetenido", "nvarchar(50)", "NULL"),
        ("MontoSujetoaRetencion", "decimal(18, 2)", "NULL"),
        ("TipoCuentaTercero", "nvarchar(50)", "NULL"),
        ("NumeroCuentaTercero", "nvarchar(50)", "NULL"),
        ("NombrePropietarioCuenta", "nvarchar(255)", "NULL"),
        ("DocumentoIdentidadPropietario", "nvarchar(50)", "NULL"),
        ("NombreBanco", "nvarchar(255)", "NULL"),
        ("NumeroCheque", "nvarchar(50)", "NULL"),
        ("MontoEfectivo", "decimal(18, 2)", "NULL"),
        ("MontoCheque", "decimal(18, 2)", "NULL"),
        ("MontoAbono", "decimal(18, 2)", "NULL"),
        ("MontoDebito", "decimal(18, 2)", "NULL"),
        ("MontoCredito", "decimal(18, 2)", "NULL"),
        ("TipoMonedaOtraMoneda", "nvarchar(50)", "NULL"),
        ("TasaCambioOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoGravadoTotalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoGravado1OtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoGravado2OtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoGravado3OtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoExentoOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoItbisTotalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoItbis1OtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoItbis2OtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoItbis3OtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoAdicionalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoAdicionalTablaOtraMoneda", "decimal(18, 2)", "NULL"),
        ("TipoImpuestoOtraMoneda1", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicionalOtraMoneda1", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda1", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda1", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesOtraMoneda1", "decimal(18, 2)", "NULL"),
        ("TipoImpuestoOtraMoneda2", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicionalOtraMoneda2", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda2", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda2", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesOtraMoneda2", "decimal(18, 2)", "NULL"),
        ("TipoImpuestoOtraMoneda3", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicionalOtraMoneda3", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda3", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda3", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesOtraMoneda3", "decimal(18, 2)", "NULL"),
        ("TipoImpuestoOtraMoneda4", "nvarchar(50)", "NULL"),
        ("TasaImpuestoAdicionalOtraMoneda4", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoOtraMoneda4", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda4", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesOtraMoneda4", "decimal(18, 2)", "NULL"),
        ("MontoImpuestosAdicionalTotalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoEspecificoTotalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("MontoImpuestoSelectivoConsumoAdvaloremTotalOtraMoneda", "decimal(18, 2)", "NULL"),
        ("OtrosImpuestosAdicionalesOtraMonedaTotal", "decimal(18, 2)", "NULL"),
        ("MontoTotalOtraMoneda", "decimal(18, 2)", "NULL"),
        
        # Columnas adicionales que aparecieron en el error
        ("TipoCuentaPago", "nvarchar(50)", "NULL"),
        ("NumeroCuentaPago", "nvarchar(100)", "NULL"),
        ("BancoPago", "nvarchar(100)", "NULL"),
        ("FechaDesde", "nvarchar(50)", "NULL"),
        ("FechaHasta", "nvarchar(50)", "NULL"),
        ("TotalPaginas", "int", "NULL"),
        ("NombreComercial", "nvarchar(255)", "NULL"),
        ("Sucursal", "nvarchar(100)", "NULL"),
        ("Municipio", "nvarchar(100)", "NULL"),
        ("Provincia", "nvarchar(100)", "NULL"),
        ("WebSite", "nvarchar(255)", "NULL"),
        ("ActividadEconomica", "nvarchar(255)", "NULL"),
        ("NumeroFacturaInterna", "nvarchar(100)", "NULL"),
        ("NumeroPedidoInterno", "nvarchar(100)", "NULL"),
        ("ZonaVenta", "nvarchar(100)", "NULL"),
        ("RutaVenta", "nvarchar(100)", "NULL"),
        ("InformacionAdicionalEmisor", "nvarchar(max)", "NULL"),
        ("IdentificadorExtranjero", "nvarchar(100)", "NULL"),
        ("MunicipioComprador", "nvarchar(100)", "NULL"),
        ("ProvinciaComprador", "nvarchar(100)", "NULL"),
        ("PaisComprador", "nvarchar(100)", "NULL"),
        ("FechaEntrega", "nvarchar(50)", "NULL"),
        ("ContactoEntrega", "nvarchar(255)", "NULL"),
        ("DireccionEntrega", "nvarchar(255)", "NULL"),
        ("TelefonoAdicional", "nvarchar(50)", "NULL"),
        ("FechaOrdenCompra", "nvarchar(50)", "NULL"),
        ("NumeroOrdenCompra", "nvarchar(100)", "NULL"),
        ("CodigoInternoComprador", "nvarchar(100)", "NULL"),
        ("InformacionAdicionalComprador", "nvarchar(max)", "NULL"),
        ("FechaEmbarque", "nvarchar(50)", "NULL"),
        ("NumeroEmbarque", "nvarchar(100)", "NULL"),
        ("NumeroContenedor", "nvarchar(100)", "NULL"),
        ("NumeroReferencia", "nvarchar(100)", "NULL"),
        ("NombrePuertoEmbarque", "nvarchar(255)", "NULL"),
        ("CondicionesEntrega", "nvarchar(255)", "NULL"),
        ("TotalFob", "decimal(18, 2)", "NULL"),
        ("Seguro", "decimal(18, 2)", "NULL"),
        ("Flete", "decimal(18, 2)", "NULL"),
        ("OtrosGastos", "decimal(18, 2)", "NULL"),
        ("TotalCif", "decimal(18, 2)", "NULL"),
        ("RegimenAduanero", "nvarchar(100)", "NULL"),
        ("NombrePuertoSalida", "nvarchar(255)", "NULL"),
        ("NombrePuertoDesembarque", "nvarchar(255)", "NULL"),
        ("PesoBruto", "decimal(18, 2)", "NULL"),
        ("PesoNeto", "decimal(18, 2)", "NULL"),
        ("UnidadPesoBruto", "nvarchar(50)", "NULL"),
        ("UnidadPesoNeto", "nvarchar(50)", "NULL"),
        ("CantidadBulto", "decimal(18, 2)", "NULL"),
        ("UnidadBulto", "nvarchar(50)", "NULL"),
        ("VolumenBulto", "decimal(18, 2)", "NULL"),
        ("UnidadVolumen", "nvarchar(50)", "NULL"),
        ("ViaTransporte", "nvarchar(100)", "NULL"),
        ("PaisOrigen", "nvarchar(100)", "NULL"),
        ("DireccionDestino", "nvarchar(255)", "NULL"),
        ("PaisDestino", "nvarchar(100)", "NULL"),
        ("RNCIdentificacionCompaniaTransportista", "nvarchar(100)", "NULL"),
        ("NombreCompaniaTransportista", "nvarchar(255)", "NULL"),
        ("NumeroViaje", "nvarchar(100)", "NULL"),
        ("Conductor", "nvarchar(255)", "NULL"),
        ("DocumentoTransporte", "nvarchar(100)", "NULL"),
        ("Ficha", "nvarchar(100)", "NULL"),
        ("Placa", "nvarchar(100)", "NULL"),
        ("RutaTransporte", "nvarchar(100)", "NULL"),
        ("ZonaTransporte", "nvarchar(100)", "NULL"),
        ("NumeroAlbaran", "nvarchar(100)", "NULL"),
        ("MontoGravadoI1", "decimal(18, 2)", "NULL"),
        ("MontoGravadoI2", "decimal(18, 2)", "NULL"),
        ("MontoGravadoI3", "decimal(18, 2)", "NULL"),
        ("ITBIS1", "decimal(18, 2)", "NULL"),
        ("ITBIS2", "decimal(18, 2)", "NULL"),
        ("ITBIS3", "decimal(18, 2)", "NULL"),
        ("TotalITBIS", "decimal(18, 2)", "NULL"),
        ("TotalITBIS1", "decimal(18, 2)", "NULL"),
        ("TotalITBIS2", "decimal(18, 2)", "NULL"),
        ("TotalITBIS3", "decimal(18, 2)", "NULL"),
        ("TotalITBISRetenido", "decimal(18, 2)", "NULL"),
        ("TotalISRRetencion", "decimal(18, 2)", "NULL"),
        ("TotalITBISPercepcion", "decimal(18, 2)", "NULL"),
        ("TotalISRPercepcion", "decimal(18, 2)", "NULL"),
        ("TipoMoneda", "nvarchar(50)", "NULL"),
        ("TipoCambio", "decimal(18, 6)", "NULL"),
        ("TotalITBISOtraMoneda", "decimal(18, 2)", "NULL"),
        ("TotalITBIS1OtraMoneda", "decimal(18, 2)", "NULL"),
        ("TotalITBIS2OtraMoneda", "decimal(18, 2)", "NULL"),
        ("TotalITBIS3OtraMoneda", "decimal(18, 2)", "NULL"),
        
        # Campos adicionales para después del detalle (post-detalle)
        ("NumeroSubTotal", "decimal(18, 2)", "NULL"),
        ("SubtotalGravadoI1", "decimal(18, 2)", "NULL"),
        ("SubtotalGravadoI2", "decimal(18, 2)", "NULL"),
        ("SubtotalGravadoI3", "decimal(18, 2)", "NULL"),
        ("SubtotalExento", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis1", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis2", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis3", "decimal(18, 2)", "NULL"),
        ("SubtotalItbisTotal", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestosAdicionales", "decimal(18, 2)", "NULL"),
        ("SubtotalTotal", "decimal(18, 2)", "NULL"),
        ("RazonModificacion", "nvarchar(255)", "NULL"),
        
        # Columnas faltantes según el error
        ("DescripcionSubtotal", "nvarchar(255)", "NULL"),
        ("Orden", "int", "NULL"),
        ("SubTotalMontoGravadoTotal", "decimal(18, 2)", "NULL"),
        ("SubTotalMontoGravadoI1", "decimal(18, 2)", "NULL"),
        ("SubTotalMontoGravadoI2", "decimal(18, 2)", "NULL"),
        ("SubTotalMontoGravadoI3", "decimal(18, 2)", "NULL"),
        ("SubTotaITBIS", "decimal(18, 2)", "NULL"),
        ("SubTotaITBIS1", "decimal(18, 2)", "NULL"),
        ("SubTotaITBIS2", "decimal(18, 2)", "NULL"),
        ("SubTotaITBIS3", "decimal(18, 2)", "NULL"),
        ("SubTotalImpuestoAdicional", "decimal(18, 2)", "NULL"),
        ("MontoSubTotal", "decimal(18, 2)", "NULL"),
        ("Lineas", "int", "NULL"),
        
        # Líneas de descuento o recargo
        ("NumeroLineaDoR1", "int", "NULL"),
        ("TipoAjuste1", "nvarchar(50)", "NULL"),
        ("IndicadorNorma10071", "nvarchar(50)", "NULL"),
        ("DescripcionDescuentooRecargo1", "nvarchar(255)", "NULL"),
        ("TipoValor1", "nvarchar(50)", "NULL"),
        ("ValorDescuentooRecargo1", "decimal(18, 2)", "NULL"),
        ("MontoDescuentooRecargo1", "decimal(18, 2)", "NULL"),
        ("MontoDescuentooRecargoOtraMoneda1", "decimal(18, 2)", "NULL"),
        ("IndicadorFacturacionDescuentooRecargo1", "nvarchar(50)", "NULL"),
        
        # Líneas de descuento o recargo 2
        ("NumeroLineaDoR2", "int", "NULL"),
        ("TipoAjuste2", "nvarchar(50)", "NULL"),
        ("IndicadorNorma10072", "nvarchar(50)", "NULL"),
        ("DescripcionDescuentooRecargo2", "nvarchar(255)", "NULL"),
        ("TipoValor2", "nvarchar(50)", "NULL"),
        ("ValorDescuentooRecargo2", "decimal(18, 2)", "NULL"),
        ("MontoDescuentooRecargo2", "decimal(18, 2)", "NULL"),
        ("MontoDescuentooRecargoOtraMoneda2", "decimal(18, 2)", "NULL"),
        ("IndicadorFacturacionDescuentooRecargo2", "nvarchar(50)", "NULL"),
        
        # Totales página 1
        ("PaginaNo1", "int", "NULL"),
        ("NoLineaDesde1", "int", "NULL"),
        ("NoLineaHasta1", "int", "NULL"),
        ("SubtotalMontoGravadoPagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado1Pagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado2Pagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado3Pagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalExentoPagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalItbisPagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis1Pagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis2Pagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis3Pagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoAdicionalPagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoAdicionalPaginaTabla1", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoSelectivoConsumoEspecificoPagina11", "decimal(18, 2)", "NULL"),
        ("SubtotalOtrosImpuesto11", "decimal(18, 2)", "NULL"),
        ("MontoSubtotalPagina1", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoNoFacturablePagina1", "decimal(18, 2)", "NULL"),
        
# Totales página 2
        ("PaginaNo2", "int", "NULL"),
        ("NoLineaDesde2", "int", "NULL"),
        ("NoLineaHasta2", "int", "NULL"),
        ("SubtotalMontoGravadoPagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado1Pagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado2Pagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoGravado3Pagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalExentoPagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalItbisPagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis1Pagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis2Pagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalItbis3Pagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoAdicionalPagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalImpuestoSelectivoConsumoEspecificoPagina21", "decimal(18, 2)", "NULL"),
        ("SubtotalOtrosImpuesto21", "decimal(18, 2)", "NULL"),
        ("MontoSubtotalPagina2", "decimal(18, 2)", "NULL"),
        ("SubtotalMontoNoFacturablePagina2", "decimal(18, 2)", "NULL"),
        
        # Campos de modificación
        ("NCFModificado", "nvarchar(100)", "NULL"),
        ("RNCOtroContribuyente", "nvarchar(50)", "NULL"),
        ("FechaNCFModificado", "nvarchar(50)", "NULL"),
        ("CodigoModificacion", "nvarchar(50)", "NULL"),
        ("ConteoImpresiones", "int", "default 0"),
        ("ResultadoEstadoFiscal", "varchar(max)", "NULL"),
        ("EstadoFiscal", "int", "DEFAULT 1"),
        ("Estadoimpresion", "int", "DEFAULT 1"),
        ("MontoDGII", "numeric(18,4)", "NULL"), 
        ("MontoITBISDGII", "numeric(18,4)", "NULL"),
        ("URLQR", "char(255)", "NULL"),
        ("fechacreacion", "DATETIME", "DEFAULT GETDATE()"),
        ("CodigoSeguridad", "char(100)", "NULL"),
        ("CodigoSeguridadCF", "char(10)", "NULL"),
        ("Trackid", "char(255)", "NULL"),
        ("FechaFirma", "char(50)", "NULL"),
    ]
    
    # Definir todas las columnas que debe tener la tabla Detalle
    columnas_detalle = [
        ("DetalleID", "int", "IDENTITY(1,1) PRIMARY KEY"),
        ("TipoeCF", "nvarchar(50)", "NULL"),
        ("ENCF", "nvarchar(100)", "NULL"),
        ("RNCEmisor", "nvarchar(50)", "NULL"),
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
        ("DescripcionItem", "nvarchar(1000)", "NULL"),
        ("CantidadItem", "decimal(18, 2)", "NULL"),
        ("UnidadMedida", "nvarchar(50)", "NULL"),
        ("CantidadReferencia", "decimal(18, 2)", "NULL"),
        ("UnidadReferencia", "nvarchar(50)", "NULL"),
        ("Subcantidad", "decimal(18, 2)", "NULL"),
        ("CodigoSubcantidad", "nvarchar(50)", "NULL"),
        ("GradosAlcohol", "decimal(18, 2)", "NULL"),
        ("PrecioUnitarioReferencia", "decimal(18, 2)", "NULL"),
        ("FechaElaboracion", "nvarchar(50)", "NULL"),  # Cambiado a nvarchar para evitar problemas
        ("FechaVencimientoItem", "nvarchar(50)", "NULL"),  # Cambiado a nvarchar para evitar problemas
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
        ("MontoItem", "decimal(18, 2)", "NULL")
        ]
    
    try:
        print("Conectando a SQL Server...")
        conn = obtener_conexion_sql(servidor, base_datos, usuario, password, trusted_connection)
        cursor = conn.cursor()
        
        # 1. Crear tabla Encabezado
        print("Verificando existencia de la tabla Encabezado...")
        cursor.execute("IF OBJECT_ID('Encabezado', 'U') IS NOT NULL SELECT 1 ELSE SELECT 0")
        encabezado_existe = cursor.fetchone()[0]
        
        if encabezado_existe:
            print("La tabla Encabezado ya existe. Eliminando restricciones...")
            # Obtener todas las restricciones de clave externa que hacen referencia a la tabla Encabezado
            cursor.execute("""
            SELECT 
                fk.name as FK_NAME,
                OBJECT_NAME(fk.parent_object_id) as TABLE_NAME
            FROM 
                sys.foreign_keys as fk
            WHERE 
                OBJECT_NAME(fk.referenced_object_id) = 'FEEncabezado'
            """)
            
            fks = cursor.fetchall()
            
            # Eliminar cada restricción de clave externa
            for fk_name, table_name in fks:
                print(f"Eliminando restricción {fk_name} de la tabla {table_name}...")
                cursor.execute(f"ALTER TABLE [{table_name}] DROP CONSTRAINT [{fk_name}]")
            
            # Eliminar la tabla Encabezado
            print("Eliminando tabla Encabezado...")
            cursor.execute("DROP TABLE FEEncabezado")
            print("Tabla Encabezado eliminada exitosamente.")
        
        # Crear la tabla Encabezado
        print("Creando tabla Encabezado con todas las columnas necesarias...")
        sql_crear_encabezado = "CREATE TABLE [dbo].[FEEncabezado] (\n"
        
        # Agregar todas las columnas
        for i, (nombre_col, tipo_col, nullable) in enumerate(columnas_encabezado):
            if i > 0:
                sql_crear_encabezado += ",\n"
            sql_crear_encabezado += f"[{nombre_col}] {tipo_col} {nullable}"
        
        sql_crear_encabezado += "\n)"
        
        cursor.execute(sql_crear_encabezado)
        print("Tabla Encabezado creada exitosamente.")
        
        # 2. Crear tabla Detalle
        print("Verificando existencia de la tabla Detalle...")
        cursor.execute("IF OBJECT_ID('FEDetalle', 'U') IS NOT NULL SELECT 1 ELSE SELECT 0")
        detalle_existe = cursor.fetchone()[0]
        
        if detalle_existe:
            print("La tabla Detalle ya existe. Eliminando...")
            cursor.execute("DROP TABLE FEDetalle")
            print("Tabla Detalle eliminada exitosamente.")
        
        # Crear la tabla Detalle
        print("Creando tabla Detalle con todas las columnas necesarias...")
        sql_crear_detalle = "CREATE TABLE [dbo].[FEDetalle] (\n"
        
        # Agregar todas las columnas
        for i, (nombre_col, tipo_col, nullable) in enumerate(columnas_detalle):
            if i > 0:
                sql_crear_detalle += ",\n"
            sql_crear_detalle += f"[{nombre_col}] {tipo_col} {nullable}"
        
        sql_crear_detalle += "\n)"
        
        cursor.execute(sql_crear_detalle)
        print("Tabla Detalle creada exitosamente.")
        
        conn.commit()
        print("Operación completada con éxito. Ambas tablas han sido creadas correctamente.")
        return True
        
    except Exception as e:
        print(f"Error al crear las tablas: {str(e)}")
        traceback.print_exc()
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    crear_ambas_tablas()