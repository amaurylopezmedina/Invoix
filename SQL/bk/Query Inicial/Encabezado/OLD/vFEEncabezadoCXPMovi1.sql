--Select * from cxpmovi1


create or alter view vFEEncabezadoCXPMovi1 as

WITH
  e AS (
    SELECT
      itbisenprecio,
      rnc
    FROM
      empresa
    WITH
      (NOLOCK)
  ),
 AmbienteInfo AS (
    SELECT TOP 1 
        A.AMBIENTE, 
        A.DESCRIP, 
        ISNULL(A.RUTA, '') AS RUTA 
    FROM FEAmbiente A
    -- Eliminamos el JOIN con empresa que podría estar limitando los resultados
    -- LEFT JOIN empresa E ON A.ambiente = E.Ambiente
    WHERE A.RUTA IS NOT NULL
    ORDER BY A.AMBIENTE  -- Aseguramos un orden consistente
)

----cxPmOVI1


SELECT
  cxp.documento AS NumeroFacturaInterna,
  cxp.tipomovi AS TipoDocumento,
  SUBSTRING(cxp.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxp.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  tn.Auxiliar,
  'cxpmovi1' as Tabla,
  tn.campo1,
  tn.campo2,
  cxp.ncf AS eNCF,
  cxp.FVencimientoNCF AS FechaVencimientoSecuencia,
  cxp.vence AS FechaLimitePago,
  cxp.dia AS TerminoPagoN,
  CAST(cxp.dia AS char (3)) + ' DIAS' AS TerminoPago,
  '0' AS Almacen,
  (
    CASE
      WHEN cxp.tipomovi = '03' OR cxp.tipomovi = '02' THEN 1
      ELSE 0
    END
  ) AS IndicadorNotaCredito,
  /*(
    SELECT
      TOP(1) itbisenprecio
    FROM
      dbo.empresa AS e1  WITH (NOLOCK)
    WHERE
      (cxp.RNCEmisor = rnc)
  )
  */
  0 AS IndicadorMontoGravado,
  '01' AS TipoIngresos,
  (
    CASE
      WHEN cxp.tipomovi = '07' THEN 1
      WHEN cxp.tipomovi = '03'
      OR cxp.tipomovi = '02' THEN 2
    END
  ) AS TipoPago,
  (
    CASE
      WHEN cxp.tipomovi = '07' THEN 'CONTADO'
      WHEN cxp.tipomovi = '03'
      OR cxp.tipomovi = '02' THEN 'CREDITO'
    END
  ) AS TipoPagoL,
  NULL AS TipoCuentaPago,
  NULL AS NumeroCuentaPago,
  NULL AS BancoPago,
  NULL AS FechaDesde,
  NULL AS FechaHasta,
  NULL AS TotalPaginas,
  REPLACE(cxp.RNCEmisor, '-', '') AS RNCEmisor,
  e.TipodeIngresos,
  e.IndicadorEnvioDiferido,
  e.RazonSocialEmisor,
  e.NombreComercial,
  e.Sucursal,
  e.DireccionEmisor,
  e.MunicipioFE AS Municipio,
  e.ProvinciaFE AS Provincia,
  e.CorreoEmisor,
  e.WebSite,
  e.ActividadEconomica,
  e.Tele AS TelefonoEmisor1,
  CAST('' AS CHAR(100)) AS TelefonoEmisor2,
  CAST('' AS CHAR(100)) AS TelefonoEmisor3,
  CAST('' AS CHAR(100)) AS CodigoVendedor,
  CAST('' AS CHAR(100)) AS NumeroPedidoInterno,
  CAST('' AS CHAR(100)) AS ZonaVenta,
  CAST('' AS CHAR(100)) AS RutaVenta,
  CAST('' AS CHAR(100)) AS InformacionAdicionalEmisor,
  cxp.fecha AS FechaEmision,
  REPLACE(cxp.rnc, '-', '') AS RNCComprador,
  NULL AS IdentificadorExtranjero,
  --Razon Social del Comprador			 
  (
    CASE
      WHEN isnull (sp.Nombre, '') = '' THEN cxp.nombre
      WHEN isnull (sp.Nombre, '') <> '' THEN sp.Nombre
      ELSE 'CLIENTE GENERICO'
    END
  ) AS RazonSocialComprador,
  (CASE WHEN CXP.tipomovi ='07' THEN '' ELSE sp.contacto END ) AS ContactoComprador,
  (CASE WHEN CXP.tipomovi ='07' THEN '' ELSE sp.Email END ) AS CorreoComprador,
  (CASE WHEN CXP.tipomovi ='07' THEN '' ELSE sp.Dire END ) AS DireccionComprador,
  CAST('' AS CHAR(100)) AS MunicipioComprador,
  CAST('' AS CHAR(100)) AS ProvinciaComprador,
  CAST('' AS CHAR(100)) AS PaisComprador,
  null AS FechaEntrega,
  CAST('' AS CHAR(100)) AS ContactoEntrega,
  CAST('' AS CHAR(100)) AS DireccionEntrega,
  (CASE WHEN CXP.tipomovi ='07' THEN '' ELSE sp.Tele END ) AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(100)) AS NumeroOrdenCompra,
  (CASE WHEN CXP.tipomovi ='07' THEN '' ELSE cxp.suplidor END ) AS CodigoInternoComprador,
  CAST('' AS CHAR(100)) AS ResponsablePago,
  CAST('' AS CHAR(100)) AS Informacionadicionalcomprador,
  null AS FechaEmbarque,
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
  NULL AS NombrePuertoDesembarque,
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
  NULL AS RutaTransporte,
  NULL AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  cxp.grava AS MontoGravadoTotal,
  cxp.grava AS MontoGravadoI1,
  NULL AS MontoGravadoI2,
  NULL AS MontoGravadoI3,
  NULL AS MontoExento,
  18 AS ITBIS1,
  NULL AS ITBIS2,
  NULL AS ITBIS3,
  cxp.impuesto AS TotalITBIS,
  cxp.impuesto AS TotalITBIS1,
  NULL AS TotalITBIS2,
  NULL AS TotalITBIS3,
  1 AS IndicadorMontoGravadoI18,
  NULL AS IndicadorMontoGravadoI16,
  NULL AS IndicadorMontoGravadoI0,
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
  '' AS NombreVendedor,
  (
    CASE
      WHEN cxp.tipomovi = '07'  THEN cxp.monto + cxp.itbisret+ cxp.retencion
      ELSE cxp.monto
    END
  ) AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  null AS SaldoAnterior,
  null AS MontoAvancePago,
  (
    CASE
      WHEN cxp.tipomovi = '07'  THEN cxp.monto + cxp.itbisret+ cxp.retencion
      ELSE cxp.monto
    END
  ) AS MontoPago,
  (
    CASE
      WHEN cxp.tipomovi = '07'  THEN cxp.monto + cxp.itbisret+ cxp.retencion
      ELSE cxp.monto
    END
  )  AS ValorPagar,
  cxp.itbisret AS TotalITBISRetenido,
  cxp.retencion AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,
  (
    CASE
      WHEN cxp.tipomovi = '' THEN 'USD'
      WHEN cxp.tipomovi = '03'
      OR cxp.tipomovi = '02' THEN 'DOP'
      ELSE 'DOP'
    END
  ) AS TipoMoneda,
  (
    CASE
      WHEN cxp.tipomovi = '' THEN 'DOLAR ESTADOUNIDENSE'
      WHEN cxp.tipomovi = '03'
      OR cxp.tipomovi = '02' THEN 'PESO DOMINICANO'
      ELSE 'PESO DOMINICANO'
    END
  ) AS TipoMonedaL,
  COALESCE(cxp.tasa, 0.00) AS TipoCambio,
  NULL AS MontoGravadoTotalOtraMoneda,
  NULL AS MontoGravado1OtraMoneda,
  NULL AS MontoGravado2OtraMoneda,
  NULL AS MontoGravado3OtraMoneda,
  NULL AS MontoExentoOtraMoneda,
  NULL AS TotalITBISOtraMoneda,
  NULL AS TotalITBIS1OtraMoneda,
  NULL AS TotalITBIS2OtraMoneda,
  NULL AS TotalITBIS3OtraMoneda,
  NULL AS MontoImpuestoAdicionalOtraMoneda,
  (
    CASE
      WHEN COALESCE(cxp.tasa, 0.00) = 0 THEN 0
      ELSE cxp.monto
    END
  ) AS MontoTotalOtraMoneda,


			 --NCF de la factura que se le esta aplicando la NC
			 cxp.NCF1 AS NCFModificado,
			 
			 --RNCOtroContribuyente
     		 REPLACE(cxp.rnc, '-', '') AS RNCOtroContribuyente,
			 --Fecha de la factura que se le esta aplicando la NC
			 cxpd.fecha AS FechaNCFModificado,
			 

			 
			 --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
			 --3: Corrige montos del NCF modificado
			 3 AS CodigoModificacion, 
			 
			 --Numero de de la factura que se le esta aplicando la NC
			 cxpd.documento1 AS NumeroDocumentoNCFModificado, 
			 
			 --Monto de la factura que se le esta aplicando la NC
			 cxpd.monto1 as MontoNCFModificado,

			 --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
			 cxpd.abono as AbonoNCFModificado,
			 
			 --Monto de descuento a la factura que se le esta aplicando la NC
			 cxpd.descuen1 as DescuentoNCFModificado,

			 --Monto Pendinete de la factura que se le esta aplicando la NC
			 cxpd.pendiente as PendienteNCFModificado,

			 --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
			 cxp.concepto AS RazonModificacion, 
			 

  
  
  cxp.fechacreacion,
  cxp.Trackid,
  cxp.FechaFirma,
  cxp.CodigoSeguridad,
  cxp.CodigoSeguridadCF,
  cxp.Estadoimpresion as EstadoImpresion,
  NULL AS ConteoImpresiones,
  cxp.EstadoFiscal,
    CASE
        WHEN SUBSTRING(cxp.ncf, 2, 2) = '32' AND cxp.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(cxp.rncemisor),
                '&ENCF=', TRIM(cxp.ncf),
                '&MontoTotal=', cxp.monto,
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(cxp.CodigoSeguridad))
            )
        WHEN SUBSTRING(cxp.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(cxp.rncemisor),
                '&ENCF=', TRIM(cxp.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(cxp.fecha),
                '&MontoTotal=', cxp.monto,
                '&FechaFirma=', REPLACE(TRIM(cxp.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](cxp.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(cxp.rncemisor),
                '&RncComprador=', TRIM(cxp.cedula),
                '&ENCF=', TRIM(cxp.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(cxp.fecha),
                '&MontoTotal=', cxp.monto,
                '&FechaFirma=', REPLACE(TRIM(cxp.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(cxp.CodigoSeguridad))
            )
    END AS URLQR,
	'' AS Observaciones,
  cxp.creado AS Creadopor,
  '' AS ModificadoPor,
  '' AS NotaPermanente,
  '' as NotaPago
FROM
  dbo.cxpmovi1 AS cxp  WITH (NOLOCK)
  LEFT OUTER JOIN dbo.sis_TipoNCF AS tn ON tn.Codigo = SUBSTRING(cxp.ncf, 2, 2)
  LEFT OUTER JOIN dbo.empresa AS e ON cxp.RNCEmisor = e.rnc
  LEFT OUTER JOIN dbo.suplidor AS sp ON sp.suplidor = cxp.suplidor
  LEFT JOIN cxpdetalle as cxpd on cxpd.Documento1= cxp.Documento1 and cxpd.tipomovi1 = '07'
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxp.tipomovi IN ('07'))
  AND (cxp.ncf IS NOT NULL)
  AND (cxp.ncf <> '')
  AND (cxp.EstadoFiscal IS NOT NULL)




