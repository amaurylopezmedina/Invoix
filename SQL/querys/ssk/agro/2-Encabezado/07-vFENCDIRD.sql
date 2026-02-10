CREATE OR ALTER VIEW vFENCDIRD AS 
--Nota de credito directo 
--Movimiento 02
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
 --Datos de Tradetalle
 --Datos de las tablas para construir las NC
SELECT
  cxc.documento AS NumeroFacturaInterna,
  cxc.tipomovi2 AS TipoDocumento,
  SUBSTRING(cxc.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxc.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  '' as idfe,
  tn.Auxiliar,
  'CXCMOVI1' AS Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
  cxc.ncf AS eNCF,
  cxc.FVencimientoNCF AS FechaVencimientoSecuencia,
  cxc.vence AS FechaLimitePago,
  cxc.dia AS TerminoPagoN,
  CAST(cxc.dia AS char (3)) + ' DIAS' AS TerminoPago,
  cxc.ALMACEN AS Almacen,
      (
	CASE
      WHEN DATEDIFF(DAY, cxcd.fecha, cxc.fecha) >30 THEN 1
	  ELSE 0
    END
  ) AS IndicadorNotaCredito,
  e.itbisenprecio AS IndicadorMontoGravado,
  '01' AS TipoIngresos,
  2 AS TipoPago, 
  'CREDITO' AS TipoPagoL,
  NULL AS TipoCuentaPago,
  NULL AS NumeroCuentaPago,
  NULL AS BancoPago,
  NULL AS FechaDesde,
  NULL AS FechaHasta,
  NULL AS TotalPaginas,
  REPLACE(cxc.RNCEmisor, '-', '') AS RNCEmisor,
  e.TipodeIngresos,
  e.IndicadorEnvioDiferido,

  e.nombre as RazonSocialEmisor,
  CAST('' AS CHAR(1)) AS NombreComercial,
  CAST('' AS CHAR(1)) AS Sucursal,
  e.dire as DireccionEmisor,
  CAST('' AS CHAR(1)) AS Municipio,
  CAST('' AS CHAR(1)) AS Provincia,
  CAST('' AS CHAR(1)) as CorreoEmisor,
  CAST('' AS CHAR(1)) as WebSite,
  CAST('' AS CHAR(1)) as ActividadEconomica,
  e.Tele  AS TelefonoEmisor1,

  CAST('' AS CHAR(1)) AS TelefonoEmisor2,
  CAST('' AS CHAR(1)) AS TelefonoEmisor3,
  CAST('' AS CHAR(1))  AS CodigoVendedor,
  CAST('' AS CHAR(1)) AS NumeroPedidoInterno,
  CAST('' AS CHAR(1)) AS ZonaVenta,
  CAST('' AS CHAR(1)) AS RutaVenta,
  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,
  cxc.fecha AS FechaEmision,
  REPLACE(TRIM(C.rnc), '-', '') AS RNCComprador,
  null AS IdentificadorExtranjero,
  --Razon Social del Comprador			 
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN cxc.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE'
    END
  ) AS RazonSocialComprador,
  c.contacto AS ContactoComprador,
  '' AS CorreoComprador,
  c.Dire AS DireccionComprador,
  CAST('' AS CHAR(1)) AS MunicipioComprador, 
  CAST('' AS CHAR(1)) AS ProvinciaComprador,
  CAST('' AS CHAR(1)) AS PaisComprador,
  null AS FechaEntrega,
  CAST('' AS CHAR(1))   AS ContactoEntrega,
  CAST('' AS CHAR(1))  AS DireccionEntrega,
  c.Tele AS TelefonoAdicional,
  NULL AS FechaOrdenCompra,
  CAST('' AS CHAR(1)) AS NumeroOrdenCompra,
  cxc.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(1)) AS ResponsablePago,
  CAST('' AS CHAR(1)) AS Informacionadicionalcomprador,
  null AS FechaEmbarque,
  CAST('' AS CHAR(1)) AS NumeroEmbarque,
  CAST('' AS CHAR(1)) AS NumeroContenedor,
  CAST('' AS CHAR(1)) AS NumeroReferencia,
  CAST('' AS CHAR(1)) AS NombrePuertoEmbarque,
  CAST('' AS CHAR(1)) AS CondicionesEntrega,
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
  null AS ZonaTransporte,
  NULL AS NumeroAlbaran,
    '' AS NombreVendedor,

--Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  0 as  MontoGravadoTotal,
  0 as MontoGravadoI1, --18
  0 as MontoGravadoI2, -- 16
  0 as MontoGravadoI3,  -- Exportacion
  cxc.monto as MontoExento,
  0 as ITBIS1,
  0 as ITBIS2,
  0 as ITBIS3,
  0 as TotalITBIS,
  0 as TotalITBIS1,
  0 as TotalITBIS2,
  0 as TotalITBIS3,
  0 as IndicadorMontoGravadoI18,
  0 as IndicadorMontoGravadoI16,
  0 as IndicadorMontoGravadoINF,
  0 as IndicadorMontoGravadoIEX,
  1 as IndicadorMontoGravadoIE,

  NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
  --Indicacion de Tipo de Moneda
  'DOP' AS TipoMoneda,
  --Descripcion del tipo de moneda
 'PESOS DOMINICANO' AS TipoMonedaL,
  --Tipo de Cambio (Tasa)
  1 AS TipoCambio,
  --Montos expresado en otra Moneda
  NULL as MontoGravadoTotalOtraMoneda,
  NULL as MontoGravado1OtraMoneda,
  NULL as MontoGravado2OtraMoneda,
  NULL as MontoGravado3OtraMoneda,
  NULL as MontoExentoOtraMoneda,
  NULL as TotalITBISOtraMoneda,
  NULL as TotalITBIS1OtraMoneda,
  NULL as TotalITBIS2OtraMoneda,
  NULL as TotalITBIS3OtraMoneda,
  NULL AS MontoImpuestoAdicionalOtraMoneda,
  NULL AS MontoTotalOtraMoneda,
  
  cxc.monto AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  cxc.monto AS MontoPago,
  cxc.monto as ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,
  --NCF de la factura que se le esta aplicando la NC
  cxc.ncf1 AS NCFModificado,
  --RNC del NCF afectado
  /*REPLACE(c.rnc, '-', '')*/ '' as RNCOtroContribuyente,
  --Fecha de la factura que se le esta aplicando la NC
  cxcd.fecha1 AS FechaNCFModificado,
  --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
  --3: Corrige montos del NCF modificado
  3 AS CodigoModificacion,
  --Numero de de la factura que se le esta aplicando la NC
  cxcd.Documento1 AS NumeroDocumentoNCFModificado,
  --Monto de la factura que se le esta aplicando la NC
  cxcd.monto1 AS MontoNCFModificado,
  --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
  cxcd.abono AS AbonoNCFModificado,
  --Monto de descuento a la factura que se le esta aplicando la NC
  cxcd.descuen1 AS DescuentoNCFModificado,
  --Monto Pendinete de la factura que se le esta aplicando la NC
  cxcd.pendiente AS PendienteNCFModificado,
  --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
  cxc.concepto AS RazonModificacion,
  cxc.fechacreacion,
  cxc.Trackid,
  cxc.FechaFirma,
  cxc.CodigoSeguridad,
  cxc.CodigoSeguridadCF,
  cxc.Estadoimpresion AS EstadoImpresion,
  NULL AS ConteoImpresiones,
  cxc.EstadoFiscal,
  cxc.ResultadoEstadoFiscal,
  cxc.MontoDGII,
  cxc.MontoITBISDGII,		 
    CASE
        WHEN SUBSTRING(cxc.ncf, 2, 2) = '32' AND cxc.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(cxc.rncemisor),
                '&ENCF=', TRIM(cxc.ncf),
                '&MontoTotal=', round(cxc.monto,2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(cxc.CodigoSeguridad))
            )
        WHEN SUBSTRING(cxc.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(cxc.rncemisor),
                '&ENCF=', TRIM(cxc.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(cxc.fecha),
                '&MontoTotal=', round(cxc.monto,2),
                '&FechaFirma=', REPLACE(TRIM(cxc.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](cxc.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(cxc.rncemisor),
				CASE 
					WHEN LEN(TRIM(REPLACE(C.rnc, '-', ''))) > 0 
					THEN CONCAT('&RncComprador=', REPLACE(TRIM(C.rnc), '-', ''))
                ELSE '' 
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(cxc.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(cxc.fecha),
                '&MontoTotal=', round(cxc.monto,2),
                '&FechaFirma=', REPLACE(TRIM(cxc.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(cxc.CodigoSeguridad))
            )
    END  AS URLQR ,
  '' AS Observaciones,
  cxc.creado AS Creadopor,
  '' AS Usuario,
  '' AS ModificadoPor,
  '' as Cajero,
  '' AS NotaPermanente,
  '' as NotaPago,
  '' as NotaAntesDeProductos,
  CXC.pccreado as EquipoImpresion



FROM
  dbo.cxcmovi1 AS cxc WITH (NOLOCK) 
  LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(cxc.ncf, 2, 2) 
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cxc.RNCEmisor = e.rnc 
  LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON trim(c.cliente) = trim(cxc.cliente)
  LEFT OUTER JOIN cxcdetalle1 AS cxcd ON trim(cxc.documento) = trim(cxcd.documento) AND trim(cxc.tipomovi) = trim(cxcd.tipomovi)
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxc.tipomovi2 IN ( '02'))
  --and (COALESCE(cxc.tasa, 1.00) =1 OR COALESCE(cxc.tasa, 1.00) = 0)
  AND (cxc.ncf IS NOT NULL)
  AND (cxc.ncf <> '')
  AND (cxc.EstadoFiscal IS NOT NULL)

