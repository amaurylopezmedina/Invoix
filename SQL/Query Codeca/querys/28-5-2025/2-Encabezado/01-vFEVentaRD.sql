CREATE OR ALTER VIEW   vFEVentaRD AS 
--Facturas a credito y contado en pesos 
WITH
 e AS (
    SELECT top 1
      itbisenprecio,
      trim(rnc)   as rnc ,
	  ambiente,
	  nota
    FROM empresa WITH (NOLOCK)
  ), 
 AmbienteInfo AS ( Select top 1
        A.AMBIENTE   as AMBIENTE, 
        A.DESCRIP   as DESCRIP, 
        ISNULL(A.RUTA, '')  AS RUTA 
    FROM FEAmbiente A WITH (NOLOCK)
	LEFT JOIN e WITH (NOLOCK) on  a.ambiente = e.ambiente 
    WHERE A.RUTA IS NOT NULL
	and a.ambiente = e.ambiente
)
SELECT
  tr.numero AS NumeroFacturaInterna,
  tr.tipo AS TipoDocumento,
  SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  tr.idfe,
  tn.Auxiliar,
  'TRANSA01' AS Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
  tr.ncf AS eNCF,
  tr.FVencimientoNCF AS FechaVencimientoSecuencia,
  tr.vence AS FechaLimitePago,
    (
    CASE
      WHEN tr.tipo = '03' THEN 0
      WHEN tr.tipo = '04' THEN tr.dia
    END
  ) AS TerminoPagoN,

    (
    CASE
      WHEN tr.tipo = '03'
    THEN ''
      WHEN tr.tipo = '04' THEN CAST(tr.dia AS char (3)) + ' DIAS'
    END
  ) AS  TerminoPago,
  
  tr.almacen AS Almacen,
  0 AS IndicadorNotaCredito,
  e.itbisenprecio AS IndicadorMontoGravado ,
  '01' AS TipoIngresos,
  (
    CASE
      WHEN tr.tipo = '03' THEN 1
      WHEN tr.tipo = '04' THEN 2
    END
  ) AS TipoPago,
  (
    CASE
      WHEN tr.tipo = '03' THEN 'CONTADO'
      WHEN tr.tipo = '04' THEN 'CREDITO'
    END
  ) AS TipoPagoL,
  NULL AS TipoCuentaPago,
  NULL AS NumeroCuentaPago,
  NULL AS BancoPago,
  NULL AS FechaDesde,
  NULL AS FechaHasta,
  NULL AS TotalPaginas,
  REPLACE(tr.RNCEmisor, '-', '') AS RNCEmisor,
  e.TipodeIngresos,
  e.IndicadorEnvioDiferido,
  --Emisor
  e.nombre as RazonSocialEmisor,
  CAST('' AS CHAR(10)) AS NombreComercial,
  CAST('' AS CHAR(10)) AS Sucursal,
  e.dire as DireccionEmisor,
  CAST('' AS CHAR(10)) AS Municipio,
  CAST('' AS CHAR(10)) AS Provincia,
  CAST('' AS CHAR(10)) as CorreoEmisor,
  CAST('' AS CHAR(10)) as WebSite,
  CAST('' AS CHAR(10)) as ActividadEconomica,
  e.Tele  AS TelefonoEmisor1,
  CAST('' AS CHAR(10)) AS TelefonoEmisor2,
  CAST('' AS CHAR(10)) AS TelefonoEmisor3,
  trim(tr.vendedor) AS CodigoVendedor,
  trim(tr.pedido) AS NumeroPedidoInterno,
  CAST('' AS CHAR(100)) AS ZonaVenta,
  CAST('' AS CHAR(100)) AS RutaVenta,
  CAST('' AS CHAR(100)) AS InformacionAdicionalEmisor,
  tr.fecha AS FechaEmision,
  (
    CASE
      WHEN ISNULL (tr.CEDULA, '') = '' THEN REPLACE(c.rnc1, '-', '')
      ELSE REPLACE(tr.CEDULA, '-', '')
    END
  ) AS RNCComprador,  --El origen del rnc cambia en cada cliente y base de datos
  
  NULL AS IdentificadorExtranjero,
  --Razon Social del Comprador
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN tr.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE GENERICO'
    END
  ) AS RazonSocialComprador,
  c.contacto AS ContactoComprador,
  CAST('' AS CHAR(100)) AS CorreoComprador,
  c.Dire AS DireccionComprador,
  CAST('' AS CHAR(100)) AS MunicipioComprador, 
  CAST('' AS CHAR(100)) AS ProvinciaComprador,
  CAST('' AS CHAR(100)) AS PaisComprador,
  null AS FechaEntrega,
  '' AS ContactoEntrega,
  trim(tr.dire) AS DireccionEntrega,
  tr.Tele AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(100)) AS NumeroOrdenCompra,
  tr.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(100)) AS ResponsablePago,
  CAST('' AS CHAR(100)) AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
  CAST('' AS CHAR(100)) AS NumeroEmbarque,
  CAST('' AS CHAR(100)) AS NumeroContenedor,
  CAST('' AS CHAR(100)) AS NumeroReferencia,
  CAST('' AS CHAR(100)) AS NombrePuertoEmbarque,
  CAST('' AS CHAR(100)) AS CondicionesEntrega,
  NULL AS TotalFob,
  NULL AS Seguro,
  NULL AS Flete,
  NULL AS OtrosGastos,
  NULL AS TotalCif,
  NULL AS RegimenAduanero,
  NULL AS NombrePuertoSalida,
  CAST('' AS CHAR(100)) AS NombrePuertoDesembarque,
  NULL AS PesoBruto,
  NULL AS PesoNeto,
  NULL AS UnidadPesoBruto,
  NULL AS UnidadPesoNeto,
  NULL AS CantidadBulto,
  NULL AS UnidadBulto,
  NULL AS VolumenBulto,
  NULL AS UnidadVolumen,
  NULL AS ViaTransporte,
  NULL AS PaisOrigen,
  NULL AS DireccionDestino,
  NULL AS PaisDestino,
  NULL AS RNCIdentificacionCompaniaTransportista,
  NULL AS NombreCompaniaTransportista,
  NULL AS NumeroViaje,
  NULL AS Conductor,
  NULL AS DocumentoTransporte,
  NULL AS Ficha,
  NULL AS Placa,
  null AS RutaTransporte,
  '' AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  
  tr.Monto-tr.itbis as  MontoGravadoTotal,
  tr.grava-tr.itbis as MontoGravadoI1, --18
  null as MontoGravadoI2, -- 16
  tr.nograva-tr.descuen as MontoGravadoI3,  -- Excento
  tr.nograva-tr.descuen as MontoExento,
  CASE
    WHEN tr.grava <> 0 THEN 18 ELSE NULL
  END
  AS ITBIS1,
  NULL AS ITBIS2,
  CASE
    WHEN tr.nograva <> 0 THEN 0 ELSE NULL
  END
  ITBIS3,
  tr.itbis  as   TotalITBIS,
  tr.itbis TotalITBIS1,
  null as TotalITBIS2,
  0 as TotalITBIS3,
    CASE
    WHEN tr.grava <> 0 THEN 1 ELSE 0
  END
  AS IndicadorMontoGravadoI18,
  0 AS IndicadorMontoGravadoI16,
  CASE
    WHEN tr.nograva <> 0 THEN 1 ELSE 0
  END
  as IndicadorMontoGravadoI0,
  NULL AS MontoImpuestoAdicional,
  NULL AS TipoImpuesto1,
  NULL AS TasaImpuestoAdicional1,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico1,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem1,
  NULL AS OtrosImpuestosAdicionales1,
  NULL AS TipoImpuesto2,
  NULL AS TasaImpuestoAdicional2,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico2,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem2,
  NULL AS OtrosImpuestosAdicionales2,
  NULL AS TipoImpuesto3,
  NULL AS TasaImpuestoAdicional3,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico3,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem3,
  NULL AS OtrosImpuestosAdicionales3,
  NULL AS TipoImpuesto4,
  NULL AS TasaImpuestoAdicional4,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico4,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem4,
  NULL AS OtrosImpuestosAdicionales4,
  NULL AS TipoImpuesto5,
  NULL AS TasaImpuestoAdicional5,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico5,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem5,
  NULL AS OtrosImpuestosAdicionales5,
  NULL AS TipoImpuesto6,
  NULL AS TasaImpuestoAdicional6,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico6,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem6,
  NULL AS OtrosImpuestosAdicionales6,
  NULL AS TipoImpuesto7,
  NULL AS TasaImpuestoAdicional7,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico7,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem7,
  NULL AS OtrosImpuestosAdicionales7,
  NULL AS TipoImpuesto8,
  NULL AS TasaImpuestoAdicional8,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico8,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem8,
  NULL AS OtrosImpuestosAdicionales8,
  NULL AS TipoImpuesto9,
  NULL AS TasaImpuestoAdicional9,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico9,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem9,
  NULL AS OtrosImpuestosAdicionales9,
  NULL AS TipoImpuesto10,
  NULL AS TasaImpuestoAdicional10,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico10,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem10,
  NULL AS OtrosImpuestosAdicionales10,
  NULL AS TipoImpuesto11,
  NULL AS TasaImpuestoAdicional11,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico11,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem11,
  NULL AS OtrosImpuestosAdicionales11,
  NULL AS TipoImpuesto12,
  NULL AS TasaImpuestoAdicional12,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico12,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem12,
  NULL AS OtrosImpuestosAdicionales12,
  NULL AS TipoImpuesto13,
  NULL AS TasaImpuestoAdicional13,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico13,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem13,
  NULL AS OtrosImpuestosAdicionales13,
  NULL AS TipoImpuesto14,
  NULL AS TasaImpuestoAdicional14,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico14,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem14,
  NULL AS OtrosImpuestosAdicionales14,
  NULL AS TipoImpuesto15,
  NULL AS TasaImpuestoAdicional15,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico15,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem15,
  NULL AS OtrosImpuestosAdicionales15,
  NULL AS TipoImpuesto16,
  NULL AS TasaImpuestoAdicional16,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico16,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem16,
  NULL AS OtrosImpuestosAdicionales16,
  NULL AS TipoImpuesto17,
  NULL AS TasaImpuestoAdicional17,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico17,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem17,
  NULL AS OtrosImpuestosAdicionales17,
  NULL AS TipoImpuesto18,
  NULL AS TasaImpuestoAdicional18,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico18,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem18,
  NULL AS OtrosImpuestosAdicionales18,
  NULL AS TipoImpuesto19,
  NULL AS TasaImpuestoAdicional19,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico19,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem19,
  NULL AS OtrosImpuestosAdicionales19,
  NULL AS TipoImpuesto20,
  NULL AS TasaImpuestoAdicional20,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico20,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem20,
  NULL AS OtrosImpuestosAdicionales20,
  NULL AS NumeroLineaDoR1,
  NULL AS TipoAjuste1,
  NULL AS IndicadorNorma10071,
  NULL AS DescripcionDescuentooRecargo1,
  NULL AS TipoValor1,
  NULL AS ValorDescuentooRecargo1,
  NULL AS MontoDescuentooRecargo1,
  NULL AS MontoDescuentooRecargoOtraMoneda1,
  NULL AS IndicadorFacturacionDescuentooRecargo1,
  NULL AS NumeroLineaDoR2,
  NULL AS TipoAjuste2,
  NULL AS IndicadorNorma10072,
  NULL AS DescripcionDescuentooRecargo2,
  NULL AS TipoValor2,
  NULL AS ValorDescuentooRecargo2,
  NULL AS MontoDescuentooRecargo2,
  NULL AS MontoDescuentooRecargoOtraMoneda2,
  NULL AS IndicadorFacturacionDescuentooRecargo2,
  NULL AS NumeroLineaDoR3,
  NULL AS TipoAjuste3,
  NULL AS IndicadorNorma10073,
  NULL AS DescripcionDescuentooRecargo3,
  NULL AS TipoValor3,
  NULL AS ValorDescuentooRecargo3,
  NULL AS MontoDescuentooRecargo3,
  NULL AS MontoDescuentooRecargoOtraMoneda3,
  NULL AS IndicadorFacturacionDescuentooRecargo3,
  NULL AS NumeroLineaDoR4,
  NULL AS TipoAjuste4,
  NULL AS IndicadorNorma10074,
  NULL AS DescripcionDescuentooRecargo4,
  NULL AS TipoValor4,
  NULL AS ValorDescuentooRecargo4,
  NULL AS MontoDescuentooRecargo4,
  NULL AS MontoDescuentooRecargoOtraMoneda4,
  NULL AS IndicadorFacturacionDescuentooRecargo4,
  NULL AS NumeroLineaDoR5,
  NULL AS TipoAjuste5,
  NULL AS IndicadorNorma10075,
  NULL AS DescripcionDescuentooRecargo5,
  NULL AS TipoValor5,
  NULL AS ValorDescuentooRecargo5,
  NULL AS MontoDescuentooRecargo5,
  NULL AS MontoDescuentooRecargoOtraMoneda5,
  NULL AS IndicadorFacturacionDescuentooRecargo5,
  NULL AS NumeroLineaDoR6,
  NULL AS TipoAjuste6,
  NULL AS IndicadorNorma10076,
  NULL AS DescripcionDescuentooRecargo6,
  NULL AS TipoValor6,
  NULL AS ValorDescuentooRecargo6,
  NULL AS MontoDescuentooRecargo6,
  NULL AS MontoDescuentooRecargoOtraMoneda6,
  NULL AS IndicadorFacturacionDescuentooRecargo6,
  NULL AS NumeroLineaDoR7,
  NULL AS TipoAjuste7,
  NULL AS IndicadorNorma10077,
  NULL AS DescripcionDescuentooRecargo7,
  NULL AS TipoValor7,
  NULL AS ValorDescuentooRecargo7,
  NULL AS MontoDescuentooRecargo7,
  NULL AS MontoDescuentooRecargoOtraMoneda7,
  NULL AS IndicadorFacturacionDescuentooRecargo7,
  NULL AS NumeroLineaDoR8,
  NULL AS TipoAjuste8,
  NULL AS IndicadorNorma10078,
  NULL AS DescripcionDescuentooRecargo8,
  NULL AS TipoValor8,
  NULL AS ValorDescuentooRecargo8,
  NULL AS MontoDescuentooRecargo8,
  NULL AS MontoDescuentooRecargoOtraMoneda8,
  NULL AS IndicadorFacturacionDescuentooRecargo8,
  NULL AS NumeroLineaDoR9,
  NULL AS TipoAjuste9,
  NULL AS IndicadorNorma10079,
  NULL AS DescripcionDescuentooRecargo9,
  NULL AS TipoValor9,
  NULL AS ValorDescuentooRecargo9,
  NULL AS MontoDescuentooRecargo9,
  NULL AS MontoDescuentooRecargoOtraMoneda9,
  NULL AS IndicadorFacturacionDescuentooRecargo9,
  NULL AS NumeroLineaDoR10,
  NULL AS TipoAjuste10,
  NULL AS IndicadorNorma100710,
  NULL AS DescripcionDescuentooRecargo10,
  NULL AS TipoValor10,
  NULL AS ValorDescuentooRecargo10,
  NULL AS MontoDescuentooRecargo10,
  NULL AS MontoDescuentooRecargoOtraMoneda10,
  NULL AS IndicadorFacturacionDescuentooRecargo10,
  NULL AS NumeroLineaDoR11,
  NULL AS TipoAjuste11,
  NULL AS IndicadorNorma100711,
  NULL AS DescripcionDescuentooRecargo11,
  NULL AS TipoValor11,
  NULL AS ValorDescuentooRecargo11,
  NULL AS MontoDescuentooRecargo11,
  NULL AS MontoDescuentooRecargoOtraMoneda11,
  NULL AS IndicadorFacturacionDescuentooRecargo11,
  NULL AS NumeroLineaDoR12,
  NULL AS TipoAjuste12,
  NULL AS IndicadorNorma100712,
  NULL AS DescripcionDescuentooRecargo12,
  NULL AS TipoValor12,
  NULL AS ValorDescuentooRecargo12,
  NULL AS MontoDescuentooRecargo12,
  NULL AS MontoDescuentooRecargoOtraMoneda12,
  NULL AS IndicadorFacturacionDescuentooRecargo12,
  NULL AS NumeroLineaDoR13,
  NULL AS TipoAjuste13,
  NULL AS IndicadorNorma100713,
  NULL AS DescripcionDescuentooRecargo13,
  NULL AS TipoValor13,
  NULL AS ValorDescuentooRecargo13,
  NULL AS MontoDescuentooRecargo13,
  NULL AS MontoDescuentooRecargoOtraMoneda13,
  NULL AS IndicadorFacturacionDescuentooRecargo13,
  NULL AS NumeroLineaDoR14,
  NULL AS TipoAjuste14,
  NULL AS IndicadorNorma100714,
  NULL AS DescripcionDescuentooRecargo14,
  NULL AS TipoValor14,
  NULL AS ValorDescuentooRecargo14,
  NULL AS MontoDescuentooRecargo14,
  NULL AS MontoDescuentooRecargoOtraMoneda14,
  NULL AS IndicadorFacturacionDescuentooRecargo14,
  NULL AS NumeroLineaDoR15,
  NULL AS TipoAjuste15,
  NULL AS IndicadorNorma100715,
  NULL AS DescripcionDescuentooRecargo15,
  NULL AS TipoValor15,
  NULL AS ValorDescuentooRecargo15,
  NULL AS MontoDescuentooRecargo15,
  NULL AS MontoDescuentooRecargoOtraMoneda15,
  NULL AS IndicadorFacturacionDescuentooRecargo15,
  NULL AS NumeroLineaDoR16,
  NULL AS TipoAjuste16,
  NULL AS IndicadorNorma100716,
  NULL AS DescripcionDescuentooRecargo16,
  NULL AS TipoValor16,
  NULL AS ValorDescuentooRecargo16,
  NULL AS MontoDescuentooRecargo16,
  NULL AS MontoDescuentooRecargoOtraMoneda16,
  NULL AS IndicadorFacturacionDescuentooRecargo16,
  NULL AS NumeroLineaDoR17,
  NULL AS TipoAjuste17,
  NULL AS IndicadorNorma100717,
  NULL AS DescripcionDescuentooRecargo17,
  NULL AS TipoValor17,
  NULL AS ValorDescuentooRecargo17,
  NULL AS MontoDescuentooRecargo17,
  NULL AS MontoDescuentooRecargoOtraMoneda17,
  NULL AS IndicadorFacturacionDescuentooRecargo17,
  NULL AS NumeroLineaDoR18,
  NULL AS TipoAjuste18,
  NULL AS IndicadorNorma100718,
  NULL AS DescripcionDescuentooRecargo18,
  NULL AS TipoValor18,
  NULL AS ValorDescuentooRecargo18,
  NULL AS MontoDescuentooRecargo18,
  NULL AS MontoDescuentooRecargoOtraMoneda18,
  NULL AS IndicadorFacturacionDescuentooRecargo18,
  NULL AS NumeroLineaDoR19,
  NULL AS TipoAjuste19,
  NULL AS IndicadorNorma100719,
  NULL AS DescripcionDescuentooRecargo19,
  NULL AS TipoValor19,
  NULL AS ValorDescuentooRecargo19,
  NULL AS MontoDescuentooRecargo19,
  NULL AS MontoDescuentooRecargoOtraMoneda19,
  NULL AS IndicadorFacturacionDescuentooRecargo19,
  NULL AS NumeroLineaDoR20,
  NULL AS TipoAjuste20,
  NULL AS IndicadorNorma100720,
  NULL AS DescripcionDescuentooRecargo20,
  NULL AS TipoValor20,
  NULL AS ValorDescuentooRecargo20,
  NULL AS MontoDescuentooRecargo20,
  NULL AS MontoDescuentooRecargoOtraMoneda20,
  NULL AS IndicadorFacturacionDescuentooRecargo20,

  TRIM(tr.venname) AS NombreVendedor,
  tr.monto  AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  (COALESCE(tr.efectivo,0.00)+COALESCE(tr.cheque,0.00)+COALESCE(tr.tarjeta,0.00)+COALESCE(tr.transferencia,0.00)) AS MontoPago,
  tr.monto AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,
  --Indicacion de Tipo de Moneda
  --tipo de Moneda
  'DOP' AS TipoMoneda,
  --Descripcion del tipo de moneda
 'PESOS DOMINICANO' AS TipoMonedaL,
  --Tipo de Cambio (Tasa)
  1 AS TipoCambio,
  --Montos expresado en otra Moneda
  null as MontoGravadoTotalOtraMoneda,
  null as MontoGravado1OtraMoneda,
  null as MontoGravado2OtraMoneda,
   null as MontoGravado3OtraMoneda,
   null as MontoExentoOtraMoneda,
   null as TotalITBISOtraMoneda,
   null as TotalITBIS1OtraMoneda,
   null as TotalITBIS2OtraMoneda,
   null as TotalITBIS3OtraMoneda,
  NULL AS MontoImpuestoAdicionalOtraMoneda,
  null AS MontoTotalOtraMoneda,
  -- Sesion de Nota de credito
  --NCF de la factura que se le esta aplicando la NC
  CAST('' AS CHAR(1)) AS NCFModificado,
  --RNC del NCF afectado
  CAST('' AS CHAR(1)) as RNCOtroContribuyente,
  --Fecha de la factura que se le esta aplicando la NC
  null AS FechaNCFModificado,
  --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
  --3: Corrige montos del NCF modificado
  NULL AS CodigoModificacion,
  --Numero de de la factura que se le esta aplicando la NC
  CAST('' AS CHAR(1)) AS NumeroDocumentoNCFModificado,
  --Monto de la factura que se le esta aplicando la NC
  0 AS MontoNCFModificado,
  --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
  0 AS AbonoNCFModificado,
  --Monto de descuento a la factura que se le esta aplicando la NC
  0 AS DescuentoNCFModificado,
  --Monto Pendinete de la factura que se le esta aplicando la NC
  0 AS PendienteNCFModificado,
  --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
  --En caso de que sea una nota de credito, enviar la razon de la modificacion 
 CAST('' AS CHAR(1)) AS RazonModificacion,
  --Datos de Facturacion Electronica
  tr.fechacreacion,
  tr.Trackid,
  tr.FechaFirma,
  tr.CodigoSeguridad,
  tr.CodigoSeguridadCF,
  tr.Estadoimpresion AS EstadoImpresion,
  tr.ConteoImpresiones,
  tr.EstadoFiscal,
    CASE
        WHEN SUBSTRING(TR.ncf, 2, 2) = '32' AND TR.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&MontoTotal=', TR.monto,
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
        WHEN SUBSTRING(TR.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', TR.monto,
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TR.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&RncComprador=', REPLACE(TRIM(c.rnc1), '-', ''),  --El origen del rnc cambia en cada cliente y base de datos
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', TR.monto,
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  tr.observa AS Observaciones,
  tr.creado AS Creadopor,
  tr.creado AS Usuario,
  tr.creado AS ModificadoPor,
  tr.creado as Cajero,
  (
    CASE
      --WHEN COALESCE(trim(tr.observa1), '') <> '' THEN tr.observa1 
      WHEN COALESCE(trim(e.nota), '') <> '' THEN e.nota 
      ELSE ''
    END
  ) AS NotaPermanente,  
  tr.Descrip1 as NotaPago,
  '' as NotaAntesDeProductos,
  tr.pccreado as EquipoImpresion
FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON c.cliente = tr.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('03', '04'))
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)
 --and tr.ncf ='E310000000009'

