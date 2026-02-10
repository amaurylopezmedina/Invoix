
create or alter view vFEInformal as

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
  cxp.documento AS NumeroFacturaInterna,
  cxp.tipomovi AS TipoDocumento,
  SUBSTRING(cxp.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxp.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  tn.Auxiliar,
  'cxpmovi1' as Tabla,
  'rncemisor' as campo1,
  'encf' as campo2,
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
  --Emisor
  e.nombre as RazonSocialEmisor,
  CAST('' AS CHAR(1)) AS NombreComercial,
  CAST('' AS CHAR(1)) AS Sucursal,
  e.dire as DireccionEmisor,
  CAST('' AS CHAR(1)) AS Municipio,
  CAST('' AS CHAR(1)) AS Provincia,
  CAST('' AS CHAR(1)) as CorreoEmisor,
  CAST('' AS CHAR(1)) as WebSite,
  CAST('' AS CHAR(1)) as ActividadEconomica,
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
  null AS MontoPago,
  null ValorPagar,
  cxp.itbisret AS TotalITBISRetenido,
  cxp.retencion AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,
 'DOP' AS TipoMoneda,
 'PESO DOMINICANO' AS TipoMonedaL,
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
  null AS MontoTotalOtraMoneda,


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
  '' AS Creadopor,
  '' AS Usuario,
  --tr.modificado AS ModificadoPor,
  '' AS ModificadoPor,
  '' as Cajero,
  /*CASE
      WHEN COALESCE(trim(tr.observa1), '') <> '' THEN tr.observa1 
      WHEN COALESCE(trim(e.nota), '') <> '' THEN e.nota 
      ELSE ''
    END
  AS NotaPermanente,  */
  --COALESCE(tr.observa, '')+'|' + COALESCE(tr.observa1, '')+'|'+ COALESCE(tr.observa3, '') 
  '' AS NotaPermanente,
  '' as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion
FROM
  dbo.cxpmovi1 AS cxp  WITH (NOLOCK)
  LEFT OUTER JOIN dbo.sis_TipoNCF AS tn ON tn.Codigo = SUBSTRING(cxp.ncf, 2, 2)
  LEFT OUTER JOIN dbo.empresa AS e ON cxp.RNCEmisor = e.rnc
  LEFT OUTER JOIN dbo.suplidor AS sp ON sp.suplidor = cxp.suplidor
  LEFT JOIN cxpdetalle as cxpd on cxpd.Documento1= cxp.Documento1 and cxpd.tipomovi1 = '07'
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxp.tipomovi IN ('07'))
  AND (cxp.informal=1)
  AND (cxp.ncf IS NOT NULL)
  AND (cxp.ncf <> '')
  AND (cxp.EstadoFiscal IS NOT NULL)
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND cxp.RNCEmisor IS NOT NULL





