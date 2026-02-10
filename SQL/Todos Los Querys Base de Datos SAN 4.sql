USE [SANSSKAgropecuaria]
GO
/****** Object:  View [dbo].[vFEEncPI]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO


CREATE   view [dbo].[vFEEncPI] as

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
),

Totales AS (

	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))

		union all
				Select  
			cc.rncemisor,cc.ncf as eNCF,cc.documento as NumeroFacturaInterna,cc.ncftipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			SUM(cc.debito - cc.credito) AS MontoTotal
		from  cajachica  AS cc WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cc.ncf, 1, 1) = 'E'
		AND RNCEmisor IS NOT NULL
		group by cc.rncemisor,cc.ncf,cc.documento,cc.ncftipo

		Union All

		Select  
			cc.rncemisor,cc.ncf as eNCF,cc.documento as NumeroFacturaInterna,cc.ncftipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			SUM(cc.debito - cc.credito) AS MontoTotal
		from  cajachica  AS cc WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cc.ncf, 1, 1) = 'E'
		AND RNCEmisor IS NOT NULL
		group by cc.rncemisor,cc.ncf,cc.documento,cc.ncftipo
		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
)

SELECT
  cxp.documento AS NumeroFacturaInterna,
  cxp.tipomovi AS TipoDocumento,
  SUBSTRING(cxp.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxp.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  null as idfe,
  tn.Auxiliar,
  'cxpmovi1' as Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
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
  REPLACE(CXP.rnc, '-', '') AS RNCComprador,
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
  --Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  Totales.MontoGravadoTotal as  MontoGravadoTotal,
  Totales.MontoGravadoI18 as MontoGravadoI1, --18
  Totales.MontoGravadoI16 as MontoGravadoI2, -- 16
  Totales.MontoGravadoIEX as MontoGravadoI3,  -- Exportacion
  Totales.MontoExento,
  Totales.ITBIS1,
  Totales.ITBIS2,
  Totales.ITBIS3,
  Totales.TotalITBIS,
  Totales.TotalITBIS1,
  Totales.TotalITBIS2,
  Totales.TotalITBIS3,
  Totales.IndicadorMontoGravadoI18,
  Totales.IndicadorMontoGravadoI16,
  Totales.IndicadorMontoGravadoINF,
  Totales.IndicadorMontoGravadoIEX,
  Totales.IndicadorMontoGravadoIE,

  NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
  --Indicacion de Tipo de Moneda
  'DOP' AS TipoMoneda,
  --Descripcion del tipo de moneda
 'PESOS DOMINICANO' AS TipoMonedaL,
  --Tipo de Cambio (Tasa)
  1 AS TipoCambio,
  --Montos expresado en otra Moneda
  Totales.MontoGravadoTotalOtraMoneda as MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda as MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda as MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda as MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda as MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda as TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda as TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda as TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda as TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda AS MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda AS MontoTotalOtraMoneda,

  cxp.monto  AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  NULL AS MontoPago,  
  NULL AS ValorPagar,
  cxp.itbisret AS TotalITBISRetenido,
  cxp.retencion AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,

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
  '' as CodigoSeguridadCF,
  cxp.Estadoimpresion AS EstadoImpresion,
  '' as ConteoImpresiones,
  cxp.EstadoFiscal,
  cxp.ResultadoEstadoFiscal,
  cxp.MontoDGII,
  cxp.MontoITBISDGII,

            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(cxp.rncemisor),
                '&RncComprador=', TRIM(cxp.rnc),
                '&ENCF=', TRIM(cxp.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(cxp.fecha),
                '&MontoTotal=', cxp.monto,
                '&FechaFirma=', REPLACE(TRIM(cxp.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(cxp.CodigoSeguridad)))
     AS URLQR,
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
   LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = cxp.RNCEmisor and Totales.eNCF = cxp.ncf
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxp.tipomovi IN ('07'))
  AND (cxp.informal=1)
  AND (cxp.ncf IS NOT NULL)
  AND (cxp.ncf <> '')
  AND (cxp.EstadoFiscal IS NOT NULL)
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND SUBSTRING(cxp.ncf, 2, 2) = '41'
  AND cxp.RNCEmisor IS NOT NULL





GO
/****** Object:  View [dbo].[vFEVentaRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO


CREATE   VIEW   [dbo].[vFEVentaRD] AS 
--Facturas a credito y contado en pesos 
--Movimeinto 03 Contado 04 Credito
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
 --Datos de las tablas para construir las Facturas 
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
  trim(tr.vendedor) AS CodigoVendedor,
  trim(tr.pedido) AS NumeroPedidoInterno,
  --LEFT(trim(tr.zona)+' '+trim(z.descrip), 20) AS ZonaVenta,
  CAST('' AS CHAR(1)) AS ZonaVenta,
  --Esta Linea se utliza en Lucas
  --LEFT(trim(tr.ruta)+' '+trim(r.descrip),20) AS RutaVenta,
  '' AS RutaVenta,

  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,

  tr.fecha AS FechaEmision,
  CASE
	WHEN   COALESCE(c.IdentificadorExtranjero, 0) = 0 then 
		CASE
			WHEN ISNULL (tr.CEDULA, '') <> '' THEN  REPLACE(TRIM(tr.CEDULA), '-', '')
			WHEN ISNULL (C.rnc, '') <> '' THEN REPLACE(TRIM(C.rnc), '-', '')
			ELSE ''
		END
  END
  AS RNCComprador,  --Identificarsi el comprador ex extranjero o tiene RNC Dominicano
  CASE
	when COALESCE(c.IdentificadorExtranjero, 0)= 1 then 
		CASE
			WHEN ISNULL (tr.CEDULA, '') <> '' THEN  REPLACE(TRIM(tr.CEDULA), '-', '')
			WHEN ISNULL (C.rnc, '') <> '' THEN REPLACE(TRIM(C.rnc), '-', '')
			ELSE '00000000000'
		END
  END
  AS IdentificadorExtranjero,
  --Razon Social del Comprador
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN tr.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE GENERICO'
    END
  ) AS RazonSocialComprador,
  '' AS ContactoComprador,
  '' AS CorreoComprador,
  tr.Dire AS DireccionComprador,
  CAST('' AS CHAR(1)) AS MunicipioComprador, 
  CAST('' AS CHAR(1)) AS ProvinciaComprador,
  CAST('' AS CHAR(1)) AS PaisComprador,
  null AS FechaEntrega,
  --Esta Linea se utiliza en Lucas
  --tr.nombrecomercial AS ContactoEntrega,
  CAST('' AS CHAR(1)) AS ContactoEntrega,
  trim(tr.dire) AS DireccionEntrega,
  tr.Tele AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(1)) AS NumeroOrdenCompra,
  tr.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(1)) AS ResponsablePago,
  CAST('' AS CHAR(1)) AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
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
  --trim(tr.ciudad) AS NombrePuertoDesembarque,
  CAST('' AS CHAR(1)) AS NombrePuertoDesembarque,
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
  '' AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  TRIM(tr.venname) AS NombreVendedor,
  
  --Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  null as  MontoGravadoTotal,
  null as MontoGravadoI1, --18
  null as MontoGravadoI2, -- 16
  null as MontoGravadoI3,  -- Exportacion
  null as MontoExento,
  null as ITBIS1,
  null  as ITBIS2,
  null  as ITBIS3,
  null  as TotalITBIS,
  null  as TotalITBIS1,
  null  as TotalITBIS2,
  null  as TotalITBIS3,
  null  as IndicadorMontoGravadoI18,
  null  as IndicadorMontoGravadoI16,
  null  as IndicadorMontoGravadoINF,
  null  as IndicadorMontoGravadoIEX,
  null as IndicadorMontoGravadoIE,

  NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
  --Indicacion de Tipo de Moneda
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
  null AS MontoImpuestoAdicionalOtraMoneda,
  null AS MontoTotalOtraMoneda,

  tr.monto  AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  NULL AS MontoPago,  
  NULL AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,

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
  
  --Seccion Informativa Facturacion Electronica
  tr.fechacreacion,
  tr.Trackid,
  tr.FechaFirma,
  tr.CodigoSeguridad,
  tr.CodigoSeguridadCF,
  tr.Estadoimpresion AS EstadoImpresion,
  tr.ConteoImpresiones,
  tr.EstadoFiscal,
  tr.ResultadoEstadoFiscal,
  tr.MontoDGII,
  tr.MontoITBISDGII,
    CASE
        WHEN SUBSTRING(TR.ncf, 2, 2) = '32' AND TR.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&MontoTotal=', round(TR.monto,2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
        WHEN SUBSTRING(TR.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TR.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
				CASE
					WHEN ISNULL (tr.CEDULA, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(tr.CEDULA), '-', ''))
					WHEN ISNULL (C.rnc, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(C.rnc), '-', ''))
					ELSE ''
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  tr.observa AS Observaciones,
  tr.creado AS Creadopor,
  tr.usuario AS Usuario,
  --tr.modificado AS ModificadoPor,
  '' AS ModificadoPor,
  tr.cajero as Cajero,
  /*CASE
      WHEN COALESCE(trim(tr.observa1), '') <> '' THEN tr.observa1 
      WHEN COALESCE(trim(e.nota), '') <> '' THEN e.nota 
      ELSE ''
    END
  AS NotaPermanente,  */
  COALESCE(tr.observa, '')+'|' + COALESCE(tr.observa1, '')+'|'+ COALESCE(tr.observa3, '') 
   AS NotaPermanente,
  tr.Descrip1 as NotaPago,
  '' as NotaAntesDeProductos,
  tr.pccreado as EquipoImpresion

FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON tr.cliente = c.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 CROSS JOIN AmbienteInfo AI 
WHERE
  tr.tipo IN ('03', '04')
  AND tr.ncf IS NOT NULL
  AND tr.ncf <> ''
  AND tr.EstadoFiscal IS NOT NULL
  AND SUBSTRING(tr.ncf, 1, 1) = 'E'
  AND tr.RNCEmisor IS NOT NULL


GO
/****** Object:  View [dbo].[vFEDevCORD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     VIEW   [dbo].[vFEDevCORD] AS 
--Nota de credito por devolucion 
--Movimiento 05
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
),

Totales AS (

	SELECT 
		numero,
		tipo,
		SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoExento,
		SUM(MontoImpuesto) as TotalITBIS,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,


		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3,

		0 AS MontoImpuestoAdicional



	FROM
		(
		Select   
			numero,tipo,i.codigodgii AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto,
			sum(COALESCE(montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		group by numero,tipo, i.codigodgii ,  i.Siglas , numero, tipo
		) AS SubConsulta
	GROUP BY numero, tipo
)
 --Datos de Tradetalle
 --Datos de las tablas para construir las NC
SELECT
  tr.numero AS NumeroFacturaInterna,
  tr.tipo AS TipoDocumento,
  SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  '' as idfe,
  tn.Auxiliar,
  'TRANSA01' AS Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
  tr.ncf AS eNCF,
  tr.FVencimientoNCF AS FechaVencimientoSecuencia,
  tr.fecha AS FechaLimitePago, -- Debe ser la misma fecha de Emision en el caso de las NC
  0 AS TerminoPagoN,
  '' AS  TerminoPago,
  tr.almacen AS Almacen,
    (
	CASE
      WHEN DATEDIFF(DAY, tr1.fecha, tr.fecha) >30 THEN 1
	  ELSE 0
    END
  ) AS IndicadorNotaCredito,
  e.itbisenprecio AS IndicadorMontoGravado,
  '01' AS TipoIngresos,
  1 AS TipoPago,  -- Hay qeu poner que tome el tipo de la factura (a credito  oa contado)
 'CONTADO' AS TipoPagoL,
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
  trim(tr.vendedor) AS CodigoVendedor,
  trim(tr.pedido) AS NumeroPedidoInterno,
  CAST('' AS CHAR(1)) AS ZonaVenta,
  CAST('' AS CHAR(1)) AS RutaVenta,
  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,
  tr.fecha AS FechaEmision,
  (
    CASE
      WHEN ISNULL (tr.CEDULA, '') = '' THEN REPLACE(TRIM(c.rnc1),'-', '')
      ELSE REPLACE(tr.CEDULA, '-', '')
    END
  ) AS RNCComprador,  --El origen del rnc cambia en cada cliente y base de datos
  NULL AS IdentificadorExtranjero,
  --Razon Social del Comprador
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN tr.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE'
    END
  ) AS RazonSocialComprador,
  '' AS ContactoComprador,
  '' AS CorreoComprador,
  c.Dire AS DireccionComprador,
  CAST('' AS CHAR(1)) AS MunicipioComprador, 
  CAST('' AS CHAR(1)) AS ProvinciaComprador,
  CAST('' AS CHAR(1)) AS PaisComprador,
  null AS FechaEntrega,
  CAST('' AS CHAR(1)) AS ContactoEntrega,
  CAST('' AS CHAR(1)) AS DireccionEntrega,
  c.Tele AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(1)) AS NumeroOrdenCompra,
  tr.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(1)) AS ResponsablePago,
  CAST('' AS CHAR(1)) AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
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
  NULL AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  TRIM(tr.venname) AS NombreVendedor,			  
  
  --Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  Totales.MontoGravadoTotal as  MontoGravadoTotal,
  Totales.MontoGravadoI18 as MontoGravadoI1, --18
  Totales.MontoGravadoI16 as MontoGravadoI2, -- 16
  Totales.MontoGravadoIEX as MontoGravadoI3,  -- Exportacion
  Totales.MontoExento,
  Totales.ITBIS1,
  Totales.ITBIS2,
  Totales.ITBIS3,
  Totales.TotalITBIS,
  Totales.TotalITBIS1,
  Totales.TotalITBIS2,
  Totales.TotalITBIS3,
  Totales.IndicadorMontoGravadoI18,
  Totales.IndicadorMontoGravadoI16,
  Totales.IndicadorMontoGravadoINF,
  Totales.IndicadorMontoGravadoIEX,
  Totales.IndicadorMontoGravadoIE,

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
  
  tr.monto AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  NULL AS MontoPago,  
  NULL AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,

  -- Sesion de Nota de credito
  --NCF de la factura que se le esta aplicando la NC
  tr1.ncf AS NCFModificado,
  --RNC del NCF afectado
  /*REPLACE(tr.cedula, '-', '')*/ '' as RNCOtroContribuyente,
  --Fecha de la factura que se le esta aplicando la NC
  tr1.fecha AS FechaNCFModificado,
  --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
  --3: Corrige montos del NCF modificado
  3 AS CodigoModificacion,
  --Numero de de la factura que se le esta aplicando la NC
  tr.documento AS NumeroDocumentoNCFModificado,
  --Monto de la factura que se le esta aplicando la NC
  tr1.monto AS MontoNCFModificado,
  --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
  0 AS AbonoNCFModificado,
  --Monto de descuento a la factura que se le esta aplicando la NC
  0 AS DescuentoNCFModificado,
  --Monto Pendinete de la factura que se le esta aplicando la NC
  0 AS PendienteNCFModificado,
  --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
  --En caso de que sea una nota de credito, enviar la razon de la modificacion 
   tr.observa AS RazonModificacion,
  --Datos de Facturacion Electronica
  tr.fechacreacion,
  tr.Trackid,
  tr.FechaFirma,
  tr.CodigoSeguridad,
  tr.CodigoSeguridadCF,
  tr.Estadoimpresion AS EstadoImpresion,
  tr.ConteoImpresiones,
  tr.EstadoFiscal,
  tr.ResultadoEstadoFiscal,
  tr.MontoDGII,
  tr.MontoITBISDGII,		 
    CASE
        WHEN SUBSTRING(TR.ncf, 2, 2) = '32' AND TR.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&MontoTotal=', round(TR.monto,2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
        WHEN SUBSTRING(TR.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TR.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
	             CONCAT('&RncComprador=', REPLACE(TRIM(c.rnc1), '-', '')),   --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  tr.observa AS Observaciones,
  tr.creado AS Creadopor,
  tr.USUARIO AS Usuario,
  tr.USUARIO AS ModificadoPor,
  tr.cajero as Cajero,
  /*(
    CASE
      WHEN COALESCE(tr.observa1, '') <> '' THEN tr.observa1
      WHEN COALESCE(tr.observa3, '') <> '' THEN tr.observa3
      ELSE ''
    END
  )*/ '' AS NotaPermanente,
  /*tr.Descrip1*/ '' as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion
FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON c.cliente = tr.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 --LEFT OUTER JOIN dbo.ruta as r  WITH (NOLOCK) on r.ruta = tr.ruta
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.numero = TR.numero and Totales.tipo = tr.tipo
 LEFT OUTER JOIN dbo.Transa01 AS tr1 WITH (nolock) ON tr1.numero = tr.documento and tr1.tipo = '03' -- Acceso a la factura a la que afecta
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('17'))
								 
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEDevCRRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     VIEW   [dbo].[vFEDevCRRD] AS 
--Nota de credito por devolucion 
--Movimiento 05
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
),

Totales AS (

	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			cxc.rncemisor,cxc.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(cxc.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(cxc.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(cxc.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.cxcmovi1 as cxc WITH (NOLOCK) ON cxc.documento = td.numero and cxc.tipomovi = td.tipo
		where estadofiscal is not null
		group by cxc.rncemisor,cxc.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(cxc.tasa, 1 ))
		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
)
 --Datos de Tradetalle
 --Datos de las tablas para construir las NC
SELECT
  cxc.documento AS NumeroFacturaInterna,
  cxc.tipomovi AS TipoDocumento,
  SUBSTRING(cxc.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxc.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  '' as idfe,
  tn.Auxiliar,
  'cxcmovi1' AS Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
  cxc.ncf AS eNCF,
  cxc.FVencimientoNCF AS FechaVencimientoSecuencia,
  cxc.fecha AS FechaLimitePago, -- Debe ser la misma fecha de Emision en el caso de las NC
  0 AS TerminoPagoN,
  '' AS  TerminoPago,
  cxc.almacen AS Almacen,
    (
	CASE
      WHEN DATEDIFF(DAY, tr1.fecha, cxc.fecha) >30 THEN 1
	  ELSE 0
    END
  ) AS IndicadorNotaCredito,
  e.itbisenprecio AS IndicadorMontoGravado,
  '01' AS TipoIngresos,
  1 AS TipoPago,  -- Hay qeu poner que tome el tipo de la factura (a credito  oa contado)
 'CONTADO' AS TipoPagoL,
  NULL AS TipoCuentaPago,
  NULL AS NumeroCuentaPago,
  NULL AS BancoPago,
  NULL AS FechaDesde,
  NULL AS FechaHasta,
  NULL AS TotalPaginas,
  REPLACE(cxc.RNCEmisor, '-', '') AS RNCEmisor,
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
  e.Tele  AS TelefonoEmisor1,
  CAST('' AS CHAR(1)) AS TelefonoEmisor2,
  CAST('' AS CHAR(1)) AS TelefonoEmisor3,
  trim(cxc.vendedor) AS CodigoVendedor,
  '' AS NumeroPedidoInterno,
  CAST('' AS CHAR(1)) AS ZonaVenta,
  CAST('' AS CHAR(1)) AS RutaVenta,
  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,
  cxc.fecha AS FechaEmision,
  REPLACE(TRIM(C.rnc),'-', '') AS RNCComprador,  --El origen del rnc cambia en cada cliente y base de datos
  NULL AS IdentificadorExtranjero,
  --Razon Social del Comprador
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN cxc.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE'
    END
  ) AS RazonSocialComprador,
  '' AS ContactoComprador,
  '' AS CorreoComprador,
  c.Dire AS DireccionComprador,
  CAST('' AS CHAR(1)) AS MunicipioComprador, 
  CAST('' AS CHAR(1)) AS ProvinciaComprador,
  CAST('' AS CHAR(1)) AS PaisComprador,
  null AS FechaEntrega,
  CAST('' AS CHAR(1)) AS ContactoEntrega,
  CAST('' AS CHAR(1)) AS DireccionEntrega,
  c.Tele AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(1)) AS NumeroOrdenCompra,
  cxc.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(1)) AS ResponsablePago,
  CAST('' AS CHAR(1)) AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
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
  NULL AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  '' AS NombreVendedor,			  
  
  --Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  Totales.MontoGravadoTotal as  MontoGravadoTotal,
  Totales.MontoGravadoI18 as MontoGravadoI1, --18
  Totales.MontoGravadoI16 as MontoGravadoI2, -- 16
  Totales.MontoGravadoIEX as MontoGravadoI3,  -- Exportacion
  Totales.MontoExento,
  Totales.ITBIS1,
  Totales.ITBIS2,
  Totales.ITBIS3,
  Totales.TotalITBIS,
  Totales.TotalITBIS1,
  Totales.TotalITBIS2,
  Totales.TotalITBIS3,
  Totales.IndicadorMontoGravadoI18,
  Totales.IndicadorMontoGravadoI16,
  Totales.IndicadorMontoGravadoINF,
  Totales.IndicadorMontoGravadoIEX,
  Totales.IndicadorMontoGravadoIE,

  NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
  --Indicacion de Tipo de Moneda
  'DOP' AS TipoMoneda,
  --Descripcion del tipo de moneda
 'PESOS DOMINICANO' AS TipoMonedaL,
  --Tipo de Cambio (Tasa)
  1 AS TipoCambio,
  --Montos expresado en otra Moneda
  Totales.MontoGravadoTotalOtraMoneda as MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda as MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda as MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda as MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda as MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda as TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda as TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda as TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda as TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda AS MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda AS MontoTotalOtraMoneda,
  
  cxc.monto AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  NULL AS MontoPago,  
  NULL AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,

  -- Sesion de Nota de credito
  --NCF de la factura que se le esta aplicando la NC
  tr1.ncf AS NCFModificado,
  --RNC del NCF afectado
  /*REPLACE(cxc.cedula, '-', '')*/ '' as RNCOtroContribuyente,
  --Fecha de la factura que se le esta aplicando la NC
  tr1.fecha AS FechaNCFModificado,
  --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
  --3: Corrige montos del NCF modificado
  (CASE
   WHEN cxc.MONTO= TR1.MONTO THEN 1
   ELSE 3
   END)
   AS CodigoModificacion,
  --Numero de de la factura que se le esta aplicando la NC
  cxc.documento1 AS NumeroDocumentoNCFModificado,
  --Monto de la factura que se le esta aplicando la NC
  tr1.monto AS MontoNCFModificado,
  --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
  0 AS AbonoNCFModificado,
  --Monto de descuento a la factura que se le esta aplicando la NC
  0 AS DescuentoNCFModificado,
  --Monto Pendinete de la factura que se le esta aplicando la NC
  0 AS PendienteNCFModificado,
  --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
  --En caso de que sea una nota de credito, enviar la razon de la modificacion 
   '' AS RazonModificacion,
  --Datos de Facturacion Electronica
  cxc.fechacreacion,
  cxc.Trackid,
  cxc.FechaFirma,
  cxc.CodigoSeguridad,
  cxc.CodigoSeguridadCF,
  cxc.Estadoimpresion AS EstadoImpresion,
  null as ConteoImpresiones,
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
					WHEN ISNULL (C.rnc, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(C.rnc), '-', ''))
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
  /*(
    CASE
      WHEN COALESCE(cxc.observa1, '') <> '' THEN cxc.observa1
      WHEN COALESCE(cxc.observa3, '') <> '' THEN cxc.observa3
      ELSE ''
    END
  )*/ '' AS NotaPermanente,
  /*cxc.Descrip1*/ '' as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion
FROM
  dbo.cxcmovi1 AS cxc WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON c.cliente = cxc.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cxc.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(cxc.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = cxc.zona
 --LEFT OUTER JOIN dbo.ruta as r  WITH (NOLOCK) on r.ruta = cxc.ruta
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = cxc.RNCEmisor and Totales.eNCF = cxc.ncf
 
 LEFT OUTER JOIN dbo.Transa01 AS tr1 WITH (nolock) ON tr1.numero = cxc.documento1 and tr1.tipo = '04' -- Acceso a la factura a la que afecta
 CROSS JOIN AmbienteInfo AI 
WHERE
  (cxc.tipomovi IN ('03'))
  AND (cxc.ncf IS NOT NULL)
  AND (cxc.ncf <> '')
  AND (cxc.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFENCDIRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE   VIEW [dbo].[vFENCDIRD] AS 
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
  cxc.tipomovi AS TipoDocumento,
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
  LEFT(cxc.concepto,90) AS RazonModificacion,
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
  '' as EquipoImpresion



FROM
  dbo.cxcmovi1 AS cxc WITH (NOLOCK) 
  LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(cxc.ncf, 2, 2) 
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cxc.RNCEmisor = e.rnc 
  LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON trim(c.cliente) = trim(cxc.cliente)
  LEFT OUTER JOIN cxcdetalle1 AS cxcd ON trim(cxc.documento) = trim(cxcd.documento) AND trim(cxc.tipomovi) = trim(cxcd.tipomovi)
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxc.tipomovi IN ( '02'))
  --and (COALESCE(cxc.tasa, 1.00) =1 OR COALESCE(cxc.tasa, 1.00) = 0)
  AND (cxc.ncf IS NOT NULL)
  AND (cxc.ncf <> '')
  AND (cxc.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEVentaUS]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     VIEW   [dbo].[vFEVentaUS] AS 
--Facturas a credito y contado en pesos 
--Movimeinto 03 Contado 04 Credito
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
),

Totales AS (

	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))
		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
)

SELECT
  tr.numero AS NumeroFacturaInterna,
  tr.tipo AS TipoDocumento,
  SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  '' as idfe,
  tn.Auxiliar,
  'TRANSA01' AS Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
  tr.ncf AS eNCF,
  tr.FVencimientoNCF AS FechaVencimientoSecuencia,
  tr.vence AS FechaLimitePago,
    (
    CASE
      WHEN tr.tipo = '33' THEN 0
      WHEN tr.tipo = '34' THEN tr.dia
    END
  ) AS TerminoPagoN,

    (
    CASE
      WHEN tr.tipo = '33'
    THEN ''
      WHEN tr.tipo = '34' THEN CAST(tr.dia AS char (3)) + ' DIAS'
    END
  ) AS  TerminoPago,
  
  tr.almacen AS Almacen,
  0 AS IndicadorNotaCredito,
  e.itbisenprecio AS IndicadorMontoGravado ,
  '01' AS TipoIngresos,
  (
    CASE
      WHEN tr.tipo = '33' THEN 1
      WHEN tr.tipo = '34' THEN 2
    END
  ) AS TipoPago,
  (
    CASE
      WHEN tr.tipo = '33' THEN 'CONTADO'
      WHEN tr.tipo = '34' THEN 'CREDITO'
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
  trim(tr.vendedor) AS CodigoVendedor,
  trim(tr.pedido) AS NumeroPedidoInterno,
  CAST('' AS CHAR(1))AS ZonaVenta,
  --Esta Linea se utliza en Lucas
  --LEFT(trim(tr.ruta)+' '+trim(r.descrip),20) AS RutaVenta,
  '' AS RutaVenta,

  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,

  tr.fecha AS FechaEmision,
  CASE
	WHEN   COALESCE(c.IdentificadorExtranjero, 0) = 0 then 
		CASE
			WHEN ISNULL (tr.CEDULA, '') <> '' THEN  REPLACE(TRIM(tr.CEDULA), '-', '')
			WHEN ISNULL (C.rnc, '') <> '' THEN REPLACE(TRIM(C.rnc), '-', '')
			ELSE ''
		END
  END
  AS RNCComprador,  --Identificarsi el comprador ex extranjero o tiene RNC Dominicano
  CASE
	when COALESCE(c.IdentificadorExtranjero, 0)= 1 then 
		CASE
			WHEN ISNULL (tr.CEDULA, '') <> '' THEN  REPLACE(TRIM(tr.CEDULA), '-', '')
			WHEN ISNULL (C.rnc, '') <> '' THEN REPLACE(TRIM(C.rnc), '-', '')
			ELSE '00000000000'
		END
  END
  AS IdentificadorExtranjero,
  --Razon Social del Comprador
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN tr.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE GENERICO'
    END
  ) AS RazonSocialComprador,
  c.contacto AS ContactoComprador,
  '' AS CorreoComprador,
  c.Dire AS DireccionComprador,
  CAST('' AS CHAR(1)) AS MunicipioComprador, 
  CAST('' AS CHAR(1)) AS ProvinciaComprador,
  CAST('' AS CHAR(1)) AS PaisComprador,
  null AS FechaEntrega,
  --Esta Linea se utiliza en Lucas
  --tr.nombrecomercial AS ContactoEntrega,
  CAST('' AS CHAR(1)) AS ContactoEntrega,
  trim(tr.dire) AS DireccionEntrega,
  tr.Tele AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(1)) AS NumeroOrdenCompra,
  tr.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(1)) AS ResponsablePago,
  CAST('' AS CHAR(1)) AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
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
  CAST('' AS CHAR(1)) AS NombrePuertoDesembarque,
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
  TRIM(tr.venname) AS NombreVendedor,
  
  --Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  Totales.MontoGravadoTotal as  MontoGravadoTotal,
  Totales.MontoGravadoI18 as MontoGravadoI1, --18
  Totales.MontoGravadoI16 as MontoGravadoI2, -- 16
  Totales.MontoGravadoIEX as MontoGravadoI3,  -- Exportacion
  Totales.MontoExento,
  Totales.ITBIS1,
  Totales.ITBIS2,
  Totales.ITBIS3,
  Totales.TotalITBIS,
  Totales.TotalITBIS1,
  Totales.TotalITBIS2,
  Totales.TotalITBIS3,
  Totales.IndicadorMontoGravadoI18,
  Totales.IndicadorMontoGravadoI16,
  Totales.IndicadorMontoGravadoINF,
  Totales.IndicadorMontoGravadoIEX,
  Totales.IndicadorMontoGravadoIE,

  NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
  --Indicacion de Tipo de Moneda
  'USD' AS TipoMoneda,
  --Descripcion del tipo de moneda
  'DOLAR ESTADOUNIDENSE' AS TipoMonedaL,
  --Tipo de Cambio (Tasa)
  tr.tasa AS TipoCambio,
 
  --Montos expresado en otra Moneda
  Totales.MontoGravadoTotalOtraMoneda as MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda as MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda as MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda as MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda as MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda as TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda as TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda as TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda as TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda AS MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda AS MontoTotalOtraMoneda,

  (tr.monto* COALESCE(tr.tasa, 1.00))  AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  NULL AS MontoPago, 
  null AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,

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
  
  --Seccion Informativa Facturacion Electronica
  tr.fechacreacion,
  tr.Trackid,
  tr.FechaFirma,
  tr.CodigoSeguridad,
  tr.CodigoSeguridadCF,
  tr.Estadoimpresion AS EstadoImpresion,
  tr.ConteoImpresiones,
  tr.EstadoFiscal,
  ResultadoEstadoFiscal,
  MontoDGII,
  MontoITBISDGII,
    CASE
        WHEN SUBSTRING(TR.ncf, 2, 2) = '32' AND TR.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&MontoTotal=', round(TR.monto,2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
        WHEN SUBSTRING(TR.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TR.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
				CASE
					WHEN ISNULL (tr.CEDULA, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(tr.CEDULA), '-', ''))
					WHEN ISNULL (C.rnc, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(C.rnc), '-', ''))
					ELSE ''
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  tr.observa AS Observaciones,
  tr.creado AS Creadopor,
  tr.usuario AS Usuario,
  --tr.modificado AS ModificadoPor,
  '' AS ModificadoPor,
  tr.cajero as Cajero,
  /*CASE
      --WHEN COALESCE(trim(tr.observa1), '') <> '' THEN tr.observa1 
      WHEN COALESCE(trim(e.nota), '') <> '' THEN e.nota 
      ELSE ''
    END
  AS NotaPermanente, */
  COALESCE(tr.observa, '')+'|' + COALESCE(tr.observa1, '')+'|'+ COALESCE(tr.observa3, '') 
  AS NotaPermanente,
  tr.Descrip1 as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion
FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON c.cliente = tr.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 --LEFT OUTER JOIN dbo.ruta as r  WITH (NOLOCK) on r.ruta = tr.ruta
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RncEmisor = TR.RncEmisor and Totales.eNCF = tr.ncf
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('33', '34'))
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)


GO
/****** Object:  View [dbo].[vFEGASMENCXP]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO



CREATE     VIEW   [dbo].[vFEGASMENCXP] AS 
--Facturas a credito y contado en pesos 
--Movimeinto 03 Contado 04 Credito
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
),
Totales AS (

	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))

		union all
				Select  
			cc.rncemisor,cc.ncf as eNCF,cc.documento as NumeroFacturaInterna,cc.ncftipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			SUM(cc.debito - cc.credito) AS MontoTotal
		from  cajachica  AS cc WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cc.ncf, 1, 1) = 'E'
		AND RNCEmisor IS NOT NULL
		group by cc.rncemisor,cc.ncf,cc.documento,cc.ncftipo

		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio)


Select 


  cxp.documento AS NumeroFacturaInterna,
  'GM' AS TipoDocumento,
  SUBSTRING(cxp.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxp.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  '' as idfe,
  tn.Auxiliar,
  'CXPMOVI1' AS Tabla,
  'rncemisor' as campo1,
  'ncf' as campo2,
  cxp.ncf AS eNCF,
  cxp.FVencimientoNCF AS FechaVencimientoSecuencia,
  cxp.vence AS FechaLimitePago,
----------------------------------------------

  0 as TerminoPagoN,
  CAST('' AS CHAR(1)) as TerminoPago,

  
  '' AS Almacen,
    0 as IndicadorNotaCredito,
    '' as IndicadorMontoGravado,
    '01' as TipoIngresos,
    1 as TipoPago,
    'CONTADO' as TipoPagoL,
    NULL as TipoCuentaPago,
    NULL as NumeroCuentaPago,
    NULL as BancoPago,
    NULL as FechaDesde,
    NULL as FechaHasta,
    NULL as TotalPaginas,
	REPLACE(cxp.RNCEmisor, '-', '') AS RNCEmisor,
    (e.TipodeIngresos) as TipodeIngresos,
	(e.IndicadorEnvioDiferido) AS IndicadorEnvioDiferido,
	  --Emisor
	(e.nombre) as RazonSocialEmisor,
	CAST('' AS CHAR(1)) AS NombreComercial,
	CAST('' AS CHAR(1)) AS Sucursal,
	(e.dire) as DireccionEmisor,
	CAST('' AS CHAR(1)) AS Municipio,
	CAST('' AS CHAR(1)) AS Provincia,
	CAST('' AS CHAR(1)) as CorreoEmisor,
	CAST('' AS CHAR(1)) as WebSite,
	CAST('' AS CHAR(1)) as ActividadEconomica,
    (e.Tele) as TelefonoEmisor1,
    CAST('' AS CHAR(1)) as TelefonoEmisor2,
    CAST('' AS CHAR(1)) as TelefonoEmisor3,
    CAST('' AS CHAR(1)) as CodigoVendedor,
    CAST('' AS CHAR(1)) as NumeroPedidoInterno,
    CAST('' AS CHAR(1)) as ZonaVenta,
    CAST('' AS CHAR(1)) as RutaVenta,
    CAST('' AS CHAR(1)) as InformacionAdicionalEmisor,
    (cxp.fecha) as FechaEmision,
    CAST('' AS CHAR(1)) as RNCComprador,
    null as IdentificadorExtranjero,
    CAST('' AS CHAR(1)) as RazonSocialComprador,
    CAST('' AS CHAR(1)) as ContactoComprador,
    CAST('' AS CHAR(1)) as CorreoComprador,
    CAST('' AS CHAR(1)) as DireccionComprador,
    CAST('' AS CHAR(1)) AS MunicipioComprador, 
    CAST('' AS CHAR(1)) as ProvinciaComprador,
    CAST('' AS CHAR(1)) as PaisComprador,
    null as FechaEntrega,
    CAST('' AS CHAR(1)) as ContactoEntrega,
    CAST('' AS CHAR(1)) as DireccionEntrega,
    CAST('' AS CHAR(1)) as TelefonoAdicional,
    null as FechaOrdenCompra,
    CAST('' AS CHAR(1)) as NumeroOrdenCompra,
    CAST('' AS CHAR(1)) as CodigoInternoComprador,
    CAST('' AS CHAR(1)) as ResponsablePago,
    CAST('' AS CHAR(1)) as Informacionadicionalcomprador,
    null as FechaEmbarque,
    CAST('' AS CHAR(1)) as NumeroEmbarque,
    CAST('' AS CHAR(1)) as NumeroContenedor,
    CAST('' AS CHAR(1)) as NumeroReferencia,
    CAST('' AS CHAR(1)) as NombrePuertoEmbarque,
    CAST('' AS CHAR(1)) as CondicionesEntrega,
    NULL as TotalFob,
    NULL as Seguro,
    NULL as Flete,
    NULL as OtrosGastos,
    NULL as TotalCif,
    NULL as RegimenAduanero,
    NULL as NombrePuertoSalida,
    NULL as NombrePuertoDesembarque,
    NULL as PesoBruto,
    NULL as PesoNeto,
    NULL as UnidadPesoBruto,
    NULL as UnidadPesoNeto,
    NULL as CantidadBulto,
    NULL as UnidadBulto,
    NULL as VolumenBulto,
    NULL as UnidadVolumen,
    NULL as ViaTransporte,
    NULL as PaisOrigen,
    NULL as DireccionDestino,
    NULL as PaisDestino,
    NULL as RNCIdentificacionCompaniaTransportista,
    NULL as NombreCompaniaTransportista,
    NULL as NumeroViaje,
    NULL as Conductor,
    NULL as DocumentoTransporte,
    NULL as Ficha,
    NULL as Placa,
    NULL as RutaTransporte,
    NULL as ZonaTransporte,
    NULL as NumeroAlbaran,
    '' as NombreVendedor,

    --Seccion de Totales
    --Verficar si a estos montos le afecta el descuento
    null as  MontoGravadoTotal,
    null as MontoGravadoI1, --18
    null as MontoGravadoI2, -- 16
    null as MontoGravadoI3,  -- Exportacion
    monto as MontoExento,
    null as ITBIS1,
    null as ITBIS2,
    0 as ITBIS3,
    0 as TotalITBIS,
    null as TotalITBIS1,
    null as  TotalITBIS2,
    null as  TotalITBIS3,
    0 as IndicadorMontoGravadoI18,
    0 as IndicadorMontoGravadoI16,
    0 as IndicadorMontoGravadoINF,
    0 as IndicadorMontoGravadoIEX,
    1 as IndicadorMontoGravadoIE,

    NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
    'DOP' as TipoMoneda,
    'PESO DOMINICANO' as TipoMonedaL,
    1 as TipoCambio,
  --Montos expresado en otra Moneda
  Totales.MontoGravadoTotalOtraMoneda as MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda as MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda as MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda as MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda as MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda as TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda as TotalITBIS1OtraMonedA,
  Totales.TotalITBIS2OtraMoneda as TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda as TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda AS MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda AS MontoTotalOtraMoneda,


    
    monto as MontoTotal,
    NULL as MontoNoFacturable,
    NULL as MontoPeriodo,
    NULL as SaldoAnterior,
    NULL as MontoAvancePago,
    NULL as MontoPago,
    NULL as ValorPagar,
    NULL as TotalITBISRetenido,
    NULL as TotalISRRetencion,
    NULL as TotalITBISPercepcion,
	NULL as TotalISRPercepcion,

	--NCF de la factura que se le esta aplicando la NC
	CAST('' AS CHAR(1)) AS NCFModificado,

	CAST('' AS CHAR(1)) as RNCOtroContribuyente,
			 
	--Fecha de la factura que se le esta aplicando la NC
	null AS FechaNCFModificado, 
			 
	--Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
	--3: Corrige montos del NCF modificado
	0 AS CodigoModificacion, 
			 
	--Numero de de la factura que se le esta aplicando la NC
	CAST('' AS CHAR(1)) AS NumeroDocumentoNCFModificado, 
			 
	--Monto de la factura que se le esta aplicando la NC
	0 as MontoNCFModificado,

	--Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
	0 as AbonoNCFModificado,
			 
	--Monto de descuento a la factura que se le esta aplicando la NC
	0 as DescuentoNCFModificado,

	--Monto Pendinete de la factura que se le esta aplicando la NC
	0 as PendienteNCFModificado,

	--Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
	CAST('' AS CHAR(1)) AS RazonModificacion, 
			 
    (cxp.fechacreacion) as fechacreacion,
    (cxp.Trackid) as Trackid,
    (cxp.FechaFirma) as FechaFirma,
    (cxp.CodigoSeguridad) as CodigoSeguridad,
    '' as CodigoSeguridadCF,
    (cxp.Estadoimpresion) as EstadoImpresion,
    NULL as ConteoImpresiones,
    (cxp.EstadoFiscal) as EstadoFiscal,
    cast((cxp.ResultadoEstadoFiscal) as nvarchar(2000)) as ResultadoEstadoFiscal,
    (cxp.MontoDGII) as MontoDGII,
    (cxp.MontoITBISDGII) as MontoITBISDGII,
    (CONCAT(
        'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?',
        'RncEmisor=', TRIM(cxp.rncemisor),
        '&ENCF=', TRIM(cxp.ncf),
        '&FechaEmision=', dbo.FNFechaDMY(cxp.fecha),
        '&MontoTotal=', round(monto,2),
        '&FechaFirma=', REPLACE(TRIM(cxp.FechaFirma), ' ', '%20'),
        '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](trim(cxp.CodigoSeguridad))
    )) as URLQR,
    '' as Observaciones,
    cxp.creado as Creadopor,
    cxp.creado AS Usuario,
    cxp.creado as ModificadoPor,
    '' as Cajero,
    '' as NotaPermanente,
    '' as NotaPago,
    '' as NotaAntesDeProductos,
    '' as EquipoImpresion

FROM cxpmovi1 as cxp

 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(cxp.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cxp.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = cxp.RNCEmisor and Totales.eNCF = cxp.ncf
 CROSS JOIN AmbienteInfo AI 

WHERE
  cxp.tipoMOVI IN ('07')
  AND cxp.gmenor = 1
  AND cxp.ncf IS NOT NULL
  AND cxp.ncf <> ''
  AND cxp.EstadoFiscal IS NOT NULL
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND cxp.RNCEmisor IS NOT NULL



  /*
  Select * from cxpmovi1 cxp

  WHERE
  cxp.tipoMOVI IN ('07')
  AND cxp.gmenor = 1
  AND cxp.ncf IS NOT NULL
  AND cxp.ncf <> ''
  AND cxp.EstadoFiscal IS NOT NULL
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND cxp.RNCEmisor IS NOT NULL

  */



GO
/****** Object:  View [dbo].[vFEGASMENCC]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO






CREATE      VIEW   [dbo].[vFEGASMENCC] as

--Caja Chica
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
),
Totales AS (

	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))

		union all
				Select  
			cc.rncemisor,cc.ncf as eNCF,cc.documento as NumeroFacturaInterna,cc.ncftipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			SUM(cc.debito - cc.credito) AS MontoTotal
		from  cajachica  AS cc WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cc.ncf, 1, 1) = 'E'
		AND RNCEmisor IS NOT NULL
		group by cc.rncemisor,cc.ncf,cc.documento,cc.ncftipo

		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio)

SELECT	
    
    MAX(cc.documento) as NumeroFacturaInterna,
    MAX(cc.ncftipo) as TipoDocumento,
    MAX(SUBSTRING(cc.ncf, 1, 1)) as TipoECFL,
    MAX(SUBSTRING(cc.ncf, 2, 2)) as TipoECF,
    MAX(tn.Descripcion) as TipoECFL1,
    MAX(tn.Descripcion) as Descripcion,
    '' as idfe,
    MAX(tn.Auxiliar) as Auxiliar,
    'CAJACHICA' as Tabla,
    'rncemisor' as campo1,
    'ncf' as campo2,
	cc.ncf AS eNCF,
    MAX(cc.FVencimientoNCF) as FechaVencimientoSecuencia,
    CAST(null AS datetime) as FechaLimitePago,
    0 as TerminoPagoN,
    CAST('' AS CHAR(1)) as TerminoPago,
    ''as Almacen,
    0 as IndicadorNotaCredito,
    '' as IndicadorMontoGravado,
    '01' as TipoIngresos,
    1 as TipoPago,
    'CONTADO' as TipoPagoL,
    NULL as TipoCuentaPago,
    NULL as NumeroCuentaPago,
    NULL as BancoPago,
    NULL as FechaDesde,
    NULL as FechaHasta,
    NULL as TotalPaginas,
	REPLACE(cc.RNCEmisor, '-', '') AS RNCEmisor,
    MAX(e.TipodeIngresos) as TipodeIngresos,
	MAX(e.IndicadorEnvioDiferido) AS IndicadorEnvioDiferido,
	  --Emisor
	max(e.nombre) as RazonSocialEmisor,
	CAST('' AS CHAR(1)) AS NombreComercial,
	CAST('' AS CHAR(1)) AS Sucursal,
	max(e.dire) as DireccionEmisor,
	CAST('' AS CHAR(1)) AS Municipio,
	CAST('' AS CHAR(1)) AS Provincia,
	CAST('' AS CHAR(1)) as CorreoEmisor,
	CAST('' AS CHAR(1)) as WebSite,
	CAST('' AS CHAR(1)) as ActividadEconomica,
    MAX(e.Tele) as TelefonoEmisor1,
    CAST('' AS CHAR(1)) as TelefonoEmisor2,
    CAST('' AS CHAR(1)) as TelefonoEmisor3,
    CAST('' AS CHAR(1)) as CodigoVendedor,
    CAST('' AS CHAR(1)) as NumeroPedidoInterno,
    CAST('' AS CHAR(1)) as ZonaVenta,
    CAST('' AS CHAR(1)) as RutaVenta,
    CAST('' AS CHAR(1)) as InformacionAdicionalEmisor,
    MAX(cc.fecha) as FechaEmision,
    CAST('' AS CHAR(1)) as RNCComprador,
    null as IdentificadorExtranjero,
    CAST('' AS CHAR(1)) as RazonSocialComprador,
    CAST('' AS CHAR(1)) as ContactoComprador,
    CAST('' AS CHAR(1)) as CorreoComprador,
    CAST('' AS CHAR(1)) as DireccionComprador,
    CAST('' AS CHAR(1)) AS MunicipioComprador, 
    CAST('' AS CHAR(1)) as ProvinciaComprador,
    CAST('' AS CHAR(1)) as PaisComprador,
    null as FechaEntrega,
    CAST('' AS CHAR(1)) as ContactoEntrega,
    CAST('' AS CHAR(1)) as DireccionEntrega,
    CAST('' AS CHAR(1)) as TelefonoAdicional,
    null as FechaOrdenCompra,
    CAST('' AS CHAR(1)) as NumeroOrdenCompra,
    CAST('' AS CHAR(1)) as CodigoInternoComprador,
    CAST('' AS CHAR(1)) as ResponsablePago,
    CAST('' AS CHAR(1)) as Informacionadicionalcomprador,
    null as FechaEmbarque,
    CAST('' AS CHAR(1)) as NumeroEmbarque,
    CAST('' AS CHAR(1)) as NumeroContenedor,
    CAST('' AS CHAR(1)) as NumeroReferencia,
    CAST('' AS CHAR(1)) as NombrePuertoEmbarque,
    CAST('' AS CHAR(1)) as CondicionesEntrega,
    NULL as TotalFob,
    NULL as Seguro,
    NULL as Flete,
    NULL as OtrosGastos,
    NULL as TotalCif,
    NULL as RegimenAduanero,
    NULL as NombrePuertoSalida,
    NULL as NombrePuertoDesembarque,
    NULL as PesoBruto,
    NULL as PesoNeto,
    NULL as UnidadPesoBruto,
    NULL as UnidadPesoNeto,
    NULL as CantidadBulto,
    NULL as UnidadBulto,
    NULL as VolumenBulto,
    NULL as UnidadVolumen,
    NULL as ViaTransporte,
    NULL as PaisOrigen,
    NULL as DireccionDestino,
    NULL as PaisDestino,
    NULL as RNCIdentificacionCompaniaTransportista,
    NULL as NombreCompaniaTransportista,
    NULL as NumeroViaje,
    NULL as Conductor,
    NULL as DocumentoTransporte,
    NULL as Ficha,
    NULL as Placa,
    NULL as RutaTransporte,
    NULL as ZonaTransporte,
    NULL as NumeroAlbaran,
    '' as NombreVendedor,

    --Seccion de Totales
    --Verficar si a estos montos le afecta el descuento
    null as  MontoGravadoTotal,
    null as MontoGravadoI1, --18
    null as MontoGravadoI2, -- 16
    null as MontoGravadoI3,  -- Exportacion
    SUM(cc.debito - cc.credito) as MontoExento,
    null as ITBIS1,
    null as ITBIS2,
    0 as ITBIS3,
    0 as TotalITBIS,
    null as TotalITBIS1,
    null as  TotalITBIS2,
    null as  TotalITBIS3,
    0 as IndicadorMontoGravadoI18,
    0 as IndicadorMontoGravadoI16,
    0 as IndicadorMontoGravadoINF,
    0 as IndicadorMontoGravadoIEX,
    1 as IndicadorMontoGravadoIE,

    NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
    'DOP' as TipoMoneda,
    'PESO DOMINICANO' as TipoMonedaL,
    1 as TipoCambio,
  --Montos expresado en otra Moneda
  SUM(Totales.MontoGravadoTotalOtraMoneda) as MontoGravadoTotalOtraMoneda,
  SUM(Totales.MontoGravado1OtraMoneda) as MontoGravado1OtraMoneda,
  SUM(Totales.MontoGravado2OtraMoneda) as MontoGravado2OtraMoneda,
  SUM(Totales.MontoGravado3OtraMoneda) as MontoGravado3OtraMoneda,
  SUM(Totales.MontoExentoOtraMoneda) as MontoExentoOtraMoneda,
  SUM(Totales.TotalITBISOtraMoneda) as TotalITBISOtraMoneda,
  SUM(Totales.TotalITBIS1OtraMoneda) as TotalITBIS1OtraMonedA,
  SUM(Totales.TotalITBIS2OtraMoneda) as TotalITBIS2OtraMoneda,
  SUM(Totales.TotalITBIS3OtraMoneda) as TotalITBIS3OtraMoneda,
  SUM(Totales.MontoImpuestoAdicionalOtraMoneda) AS MontoImpuestoAdicionalOtraMoneda,
  SUM(Totales.MontoTotalOtraMoneda) AS MontoTotalOtraMoneda,


    
    SUM(cc.debito - cc.credito) as MontoTotal,
    NULL as MontoNoFacturable,
    NULL as MontoPeriodo,
    NULL as SaldoAnterior,
    NULL as MontoAvancePago,
    NULL as MontoPago,
    NULL as ValorPagar,
    NULL as TotalITBISRetenido,
    NULL as TotalISRRetencion,
    NULL as TotalITBISPercepcion,
	NULL as TotalISRPercepcion,

	--NCF de la factura que se le esta aplicando la NC
	CAST('' AS CHAR(1)) AS NCFModificado,

	CAST('' AS CHAR(1)) as RNCOtroContribuyente,
			 
	--Fecha de la factura que se le esta aplicando la NC
	null AS FechaNCFModificado, 
			 
	--Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
	--3: Corrige montos del NCF modificado
	0 AS CodigoModificacion, 
			 
	--Numero de de la factura que se le esta aplicando la NC
	CAST('' AS CHAR(1)) AS NumeroDocumentoNCFModificado, 
			 
	--Monto de la factura que se le esta aplicando la NC
	0 as MontoNCFModificado,

	--Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
	0 as AbonoNCFModificado,
			 
	--Monto de descuento a la factura que se le esta aplicando la NC
	0 as DescuentoNCFModificado,

	--Monto Pendinete de la factura que se le esta aplicando la NC
	0 as PendienteNCFModificado,

	--Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
	CAST('' AS CHAR(1)) AS RazonModificacion, 
			 
    MAX(cc.fechacreacion) as fechacreacion,
    MAX(cc.Trackid) as Trackid,
    MAX(cc.FechaFirma) as FechaFirma,
    MAX(cc.CodigoSeguridad) as CodigoSeguridad,
    '' as CodigoSeguridadCF,
    MAX(cc.Estadoimpresion) as EstadoImpresion,
    NULL as ConteoImpresiones,
    MAX(cc.EstadoFiscal) as EstadoFiscal,
    CAST(max(cc.ResultadoEstadoFiscal) as nvarchar(2000)) as ResultadoEstadoFiscal,
    max(cc.MontoDGII) as MontoDGII,
    max(cc.MontoITBISDGII) as MontoITBISDGII,
    CONCAT(
        'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?',
        'RncEmisor=', TRIM(MAX(cc.rncemisor)),
        '&ENCF=', TRIM(MAX(cc.ncf)),
        '&FechaEmision=', dbo.FNFechaDMY(MAX(cc.fecha)),
        '&MontoTotal=', CAST(SUM(cc.debito - cc.credito) AS varchar(32)),
        '&FechaFirma=', REPLACE(TRIM(MAX(cc.FechaFirma)), ' ', '%20'),
        '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(MAX(cc.CodigoSeguridad)))
    ) AS URLQR,
    '' as Observaciones,
    max(cc.recibido) as Creadopor,
    max(cc.recibido) AS Usuario,
    max(cc.recibido) as ModificadoPor,
    '' as Cajero,
    '' as NotaPermanente,
    '' as NotaPago,
    '' as NotaAntesDeProductos,
    '' as EquipoImpresion
FROM dbo.cajachica AS cc  WITH (NOLOCK)
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn ON tn.Codigo = SUBSTRING(cc.ncf, 2, 2) 
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cc.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = cc.RNCEmisor and Totales.eNCF = cc.ncf
 CROSS JOIN AmbienteInfo AI 
WHERE cc.ncftipo IN ('GM') 
AND (cc.ncf IS NOT NULL) 
AND (cc.ncf <> '') 
AND (cc.EstadoFiscal IS NOT NULL)
AND SUBSTRING(cc.ncf, 1, 1) = 'E'
AND cc.RNCEmisor IS NOT NULL
GROUP BY  cc.RNCEmisor, cc.ncf
GO
/****** Object:  View [dbo].[vFEEncabezado]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   VIEW   [dbo].[vFEEncabezado] AS 

--Ventas en Pesos
Select * from vFEVentaRD

union all

--Ventas en Dolares
Select * from vFEVentaUS

union all

--Devoluciones a Contado
Select * from vFEDevCORD

union all

--Decoluciones a Credito
Select * from vFEDevCRRD



union all

Select * from vFENCDIRD 


Union all

--Gastos Menores

Select * from vFEGASMENCC

union all

Select * from vFEGASMENCXP

--Compras Informales


union all

Select * from vFEEncPI
GO
/****** Object:  View [dbo].[vFEDetPI]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/*Detalle de CXPMovi1*/

CREATE   view [dbo].[vFEDetPI] as

SELECT
    NULL AS NumeroLinea,
    cxp.documento AS NumeroFacturaInterna,
    cxp.tipomovi AS TipoDocumento,
    SUBSTRING (cxp.ncf, 2, 2) AS TipoECF,
    SUBSTRING (cxp.ncf, 1, 1) AS TipoECFL,
    cxp.ncf AS eNCF,
    cxp.RNCEmisor,
    CAST('' AS CHAR(100)) AS TipoCodigo1,
    CAST('' AS CHAR(100)) AS CodigoItem1,
    CAST('' AS CHAR(100)) AS TipoCodigo2,
    CAST('' AS CHAR(100)) AS CodigoItem2,
    CAST('' AS CHAR(100)) AS TipoCodigo3,
    CAST('' AS CHAR(100)) AS CodigoItem3,
    CAST('' AS CHAR(100)) AS TipoCodigo4,
    CAST('' AS CHAR(100)) AS CodigoItem4,
    CAST('' AS CHAR(100)) AS TipoCodigo5,
    CAST('' AS CHAR(100)) AS CodigoItem5,
    CASE 
    WHEN COALESCE( cxp.impuesto, 0)  >0 THEN  i.codigodgii 
    ELSE 4
    END
    AS IndicadorFacturacion,
    
    CASE 
    WHEN COALESCE( cxp.impuesto, 0)  >0 THEN  i.Siglas 
    ELSE 'E'
    END
    AS SiglasImpuesto,

    CASE 
    WHEN COALESCE( cxp.impuesto, 0)  >0 THEN  i.Descrip 
    ELSE 'EXENTO'
    END
    AS DescripcionImpuesto,


    1 AS IndicadorAgenteRetencionoPercepcion,
    cxp.itbisret AS MontoITBISRetenido,
    cxp.isr AS MontoISRRetenido,
	cxp.concepto NombreItem,
    1 AS IndicadorBienoServicio,
    NULL AS DescripcionItem,
    1 AS CantidadItem,
    '' AS UnidadMedida,
    '' as UnidadMedidaL,
    NULL AS CantidadReferencia,
    NULL AS UnidadReferencia,
    NULL AS Subcantidad1,
    NULL AS CodigoSubcantidad1,
    NULL AS Subcantidad2,
    NULL AS CodigoSubcantidad2,
    NULL AS Subcantidad3,
    NULL AS CodigoSubcantidad3,
    NULL AS Subcantidad4,
    NULL AS CodigoSubcantidad4,
    NULL AS Subcantidad5,
    NULL AS CodigoSubcantidad5,
    NULL AS GradosAlcohol,
    NULL AS PrecioUnitarioReferencia,
    NULL AS FechaElaboracion,
    NULL AS FechaVencimientoItem,
    NULL AS PesoNetoKilogramo,
    NULL AS PesoNetoMineria,
    NULL AS TipoAfiliacion,
    NULL AS Liquidacion,
    cxp.monto+cxp.isr AS PrecioUnitarioItem,
    cxp.descuen AS DescuentoMonto,

    CASE 
    WHEN COALESCE( cxp.impuesto, 0)  >0 THEN  i.pto 
    ELSE 0
    END
    AS TasaITBIS,

    CASE 
    WHEN COALESCE( cxp.impuesto, 0)  >0 THEN  1 
    ELSE 0
    END
    AS IndicadorMontoGravado,
    
    cxp.impuesto AS MontoITBIS,
    NULL AS TasaDescuento,
    (
        CASE
            WHEN ISNULL (cxp.descuen, 0) <> 0 THEN '$'
            ELSE ''
        END
    ) AS TipoSubDescuento1,
    NULL AS SubDescuentoPorcentaje1,
    (
        CASE
            WHEN ISNULL (cxp.descuen, 0) <> 0 THEN cxp.descuen
            ELSE NULL
        END
    ) AS MontoSubDescuento1,
    NULL AS TipoSubDescuento2,
    NULL AS SubDescuentoPorcentaje2,
    NULL AS MontoSubDescuento2,
    NULL AS TipoSubDescuento3,
    NULL AS SubDescuentoPorcentaje3,
    NULL AS MontoSubDescuento3,
    NULL AS TipoSubDescuento4,
    NULL AS SubDescuentoPorcentaje4,
    NULL AS MontoSubDescuento4,
    NULL AS TipoSubDescuento5,
    NULL AS SubDescuentoPorcentaje5,
    NULL AS MontoSubDescuento5,
    NULL AS MontoRecargo,
    NULL AS TipoSubRecargo1,
    NULL AS SubRecargoPorcentaje1,
    NULL AS MontoSubRecargo1,
    NULL AS TipoSubRecargo2,
    NULL AS SubRecargoPorcentaje2,
    NULL AS MontoSubRecargo2,
    NULL AS TipoSubRecargo3,
    NULL AS SubRecargoPorcentaje3,
    NULL AS MontoSubRecargo3,
    NULL AS TipoSubRecargo4,
    NULL AS SubRecargoPorcentaje4,
    NULL AS MontoSubRecargo4,
    NULL AS TipoSubRecargo5,
    NULL AS SubRecargoPorcentaje5,
    NULL AS MontoSubRecargo5,
    NULL AS TipoImpuesto1,
    NULL AS TipoImpuesto2,
    COALESCE(cxp.tasa, 1) AS TipoCambio,
    NULL AS MontoITBISOtraMoneda,
    NULL AS PrecioOtraMoneda,
    NULL AS DescuentoOtraMoneda,
    NULL AS MontoRecargoOtraMoneta,
    NULL AS MontoItemOtraMoneda,
    cxp.monto AS MontoItem,
	'' AS NotaImpresion
FROM
    cxpmovi1 cxp
    LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = '02'
WHERE
    (cxp.tipomovi IN ('07'))
    AND (cxp.ncf IS NOT NULL)
    AND (cxp.ncf <> '')
    AND (cxp.EstadoFiscal IS NOT NULL)
    and SUBSTRING (ncf, 1, 1) = 'E'
    and SUBSTRING (ncf, 2, 2) = '41'

GO
/****** Object:  View [dbo].[vFENCDIDEtRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFENCDIDEtRD] as

    SELECT
    NULL AS NumeroLinea,
    cxc.documento AS NumeroFacturaInterna,
    cxc.tipomovi AS TipoDocumento,
    SUBSTRING (cxc.ncf, 2, 2) AS TipoECF,
    SUBSTRING (cxc.ncf, 1, 1) AS TipoECFL,
    cxc.ncf AS eNCF,
    cxc.RNCEmisor,
    CAST('' AS CHAR(100)) AS TipoCodigo1,
    CAST('' AS CHAR(100)) AS CodigoItem1,
    CAST('' AS CHAR(100)) AS TipoCodigo2,
    CAST('' AS CHAR(100)) AS CodigoItem2,
    CAST('' AS CHAR(100)) AS TipoCodigo3,
    CAST('' AS CHAR(100)) AS CodigoItem3,
    CAST('' AS CHAR(100)) AS TipoCodigo4,
    CAST('' AS CHAR(100)) AS CodigoItem4,
    CAST('' AS CHAR(100)) AS TipoCodigo5,
    CAST('' AS CHAR(100)) AS CodigoItem5,
    4 AS IndicadorFacturacion,
    'E' AS SiglasImpuesto,
    'EXENTO' AS DescripcionImpuesto,
    NULL AS IndicadorAgenteRetencionoPercepcion,
    /*cxc.itbisret*/
	NULL AS MontoITBISRetenido,
    /*cxc.isr*/
	NULL AS MontoISRRetenido,
	'REBAJA DIRECTA' as NombreItem,
    1 AS IndicadorBienoServicio,
    NULL AS DescripcionItem,
    1 AS CantidadItem,
    '' AS UnidadMedida,
	'' as UnidadMedidaL,
    NULL AS CantidadReferencia,
    NULL AS UnidadReferencia,
    NULL AS Subcantidad1,
    NULL AS CodigoSubcantidad1,
    NULL AS Subcantidad2,
    NULL AS CodigoSubcantidad2,
    NULL AS Subcantidad3,
    NULL AS CodigoSubcantidad3,
    NULL AS Subcantidad4,
    NULL AS CodigoSubcantidad4,
    NULL AS Subcantidad5,
    NULL AS CodigoSubcantidad5,
    NULL AS GradosAlcohol,
    NULL AS PrecioUnitarioReferencia,
    NULL AS FechaElaboracion,
    NULL AS FechaVencimientoItem,
    NULL AS PesoNetoKilogramo,
    NULL AS PesoNetoMineria,
    NULL AS TipoAfiliacion,
    NULL AS Liquidacion,
    cxc.monto AS PrecioUnitarioItem,
    cxc.descuen AS DescuentoMonto,
    18 AS TasaITBIS,
    1 AS IndicadorMontoGravado,
    cxc.impuesto AS MontoITBIS,
    NULL AS TasaDescuento,
    (CASE WHEN ISNULL(cxc.descuen,0) <> 0 THEN '$' ELSE '' END) AS TipoSubDescuento1,
    NULL AS SubDescuentoPorcentaje1,
    (CASE WHEN ISNULL(cxc.descuen,0) <> 0 THEN cxc.descuen ELSE NULL END) AS MontoSubDescuento1,
    NULL AS TipoSubDescuento2,
    NULL AS SubDescuentoPorcentaje2,
    NULL AS MontoSubDescuento2,
    NULL AS TipoSubDescuento3,
    NULL AS SubDescuentoPorcentaje3,
    NULL AS MontoSubDescuento3,
    NULL AS TipoSubDescuento4,
    NULL AS SubDescuentoPorcentaje4,
    NULL AS MontoSubDescuento4,
    NULL AS TipoSubDescuento5,
    NULL AS SubDescuentoPorcentaje5,
    NULL AS MontoSubDescuento5,
    NULL AS MontoRecargo,
    NULL AS TipoSubRecargo1,
    NULL AS SubRecargoPorcentaje1,
    NULL AS MontoSubRecargo1,
    NULL AS TipoSubRecargo2,
    NULL AS SubRecargoPorcentaje2,
    NULL AS MontoSubRecargo2,
    NULL AS TipoSubRecargo3,
    NULL AS SubRecargoPorcentaje3,
    NULL AS MontoSubRecargo3,
    NULL AS TipoSubRecargo4,
    NULL AS SubRecargoPorcentaje4,
    NULL AS MontoSubRecargo4,
    NULL AS TipoSubRecargo5,
    NULL AS SubRecargoPorcentaje5,
    NULL AS MontoSubRecargo5,
    NULL AS TipoImpuesto1,
    NULL AS TipoImpuesto2,
    CASE
     WHEN COALESCE(cxc.tasa, 1.00) = 0 THEN 1 --SI ES CERO DEVIELVE 1
     WHEN COALESCE(cxc.tasa, 1.00) > 1 THEN cxc.tasa -- SI ES MAYOR QUE UNO DEVUELVE ;A TASA 
     ELSE COALESCE(cxc.tasa, 1.00) -- SI ES NULO DEVUELVE 1
    END
    AS TipoCambio,
    NULL AS MontoITBISOtraMoneda,
    NULL AS PrecioOtraMoneda,
    NULL AS DescuentoOtraMoneda,
    NULL AS MontoRecargoOtraMoneta,
    NULL AS MontoItemOtraMoneda,
    cxc.monto AS MontoItem,
	'' AS NotaImpresion

FROM
    cxcmovi1 cxc
    LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = '00'
WHERE
    (cxc.tipomovi IN ('02'))
--and (COALESCE(cxc.tasa, 1.00) =1 OR COALESCE(cxc.tasa, 1.00) = 0)
AND (cxc.ncf IS NOT NULL) 
AND (cxc.ncf <> '') 
AND (cxc.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEDevCRDetRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     VIEW   [dbo].[vFEDevCRDetRD] as
WITH
  e AS (  SELECT itbisenprecio, rnc FROM empresa WITH (NOLOCK)   )

SELECT
  null AS NumeroLinea,
  td.numero AS NumeroFacturaInterna,
  td.tipo AS TipoDocumento,
  SUBSTRING(cxc.ncf, 2, 2) AS TipoECF,
  SUBSTRING(cxc.ncf, 1, 1) AS TipoECFL,
  cxc.ncf AS eNCF,
  trim(cxc.RNCEmisor) as RNCEmisor ,
  CAST('Interna' AS CHAR(100)) AS TipoCodigo1,
  CAST(td.producto AS CHAR(100)) AS CodigoItem1,
  CAST('' AS CHAR(100)) AS TipoCodigo2,
  CAST('' AS CHAR(100)) AS CodigoItem2,
  CAST('' AS CHAR(100)) AS TipoCodigo3,
  CAST('' AS CHAR(100)) AS CodigoItem3,
  CAST('' AS CHAR(100)) AS TipoCodigo4,
  CAST('' AS CHAR(100)) AS CodigoItem4,
  CAST('' AS CHAR(100)) AS TipoCodigo5,
  CAST('' AS CHAR(100)) AS CodigoItem5,
  i.codigodgii AS IndicadorFacturacion,
  i.Siglas AS SiglasImpuesto,
  i.Descrip AS DescripcionImpuesto,
  NULL AS IndicadorAgenteRetencionoPercepcion,
  NULL AS MontoITBISRetenido,
  NULL AS MontoISRRetenido,
  TRIM(p.descrip) AS NombreItem,
  CASE
    p.servicio
    WHEN 0 THEN 1
    WHEN 1 THEN 2
    ELSE 1
  END AS IndicadorBienoServicio,
  NULL AS DescripcionItem,
  CASE
    WHEN td.cantidad < 0 THEN td.cantidad * - 1
    ELSE td.cantidad
  END AS CantidadItem,
  '' AS UnidadMedida,
    '' as UnidadMedidaL,

  NULL AS CantidadReferencia,
  NULL AS UnidadReferencia,
  NULL AS Subcantidad1,
  NULL AS CodigoSubcantidad1,
  NULL AS Subcantidad2,
  NULL AS CodigoSubcantidad2,
  NULL AS Subcantidad3,
  NULL AS CodigoSubcantidad3,
  NULL AS Subcantidad4,
  NULL AS CodigoSubcantidad4,
  NULL AS Subcantidad5,
  NULL AS CodigoSubcantidad5,
  NULL AS GradosAlcohol,
  NULL AS PrecioUnitarioReferencia,
  NULL AS FechaElaboracion,
  NULL AS FechaVencimientoItem,
  NULL AS PesoNetoKilogramo,
  NULL AS PesoNetoMineria,
  NULL AS TipoAfiliacion,
  NULL AS Liquidacion,
  td.precio  AS PrecioUnitarioItem,
  td.montodesc  AS DescuentoMonto,
  td.itbis AS TasaITBIS,
  e.itbisenprecio AS IndicadorMontoGravado,
  
  td.montoitbis  AS MontoITBIS,

  td.descuen AS TasaDescuento,
  '$' AS TipoSubDescuento1,
  null AS SubDescuentoPorcentaje1,
 td.montodesc AS MontoSubDescuento1,
  NULL AS TipoSubDescuento2,
  NULL AS SubDescuentoPorcentaje2,
  NULL AS MontoSubDescuento2,
  NULL AS TipoSubDescuento3,
  NULL AS SubDescuentoPorcentaje3,
  NULL AS MontoSubDescuento3,
  NULL AS TipoSubDescuento4,
  NULL AS SubDescuentoPorcentaje4,
  NULL AS MontoSubDescuento4,
  NULL AS TipoSubDescuento5,
  NULL AS SubDescuentoPorcentaje5,
  NULL AS MontoSubDescuento5,
  NULL AS MontoRecargo,
  NULL AS TipoSubRecargo1,
  NULL AS SubRecargoPorcentaje1,
  NULL AS MontoSubRecargo1,
  NULL AS TipoSubRecargo2,
  NULL AS SubRecargoPorcentaje2,
  NULL AS MontoSubRecargo2,
  NULL AS TipoSubRecargo3,
  NULL AS SubRecargoPorcentaje3,
  NULL AS MontoSubRecargo3,
  NULL AS TipoSubRecargo4,
  NULL AS SubRecargoPorcentaje4,
  NULL AS MontoSubRecargo4,
  NULL AS TipoSubRecargo5,
  NULL AS SubRecargoPorcentaje5,
  NULL AS MontoSubRecargo5,
  NULL AS TipoImpuesto1,
  NULL AS TipoImpuesto2,
  COALESCE(cxc.tasa,1) AS TipoCambio,
  null AS MontoITBISOtraMoneda,
  null AS PrecioOtraMoneda,
  null AS DescuentoOtraMoneda,
  NULL AS MontoRecargoOtraMoneta,
  null AS MontoItemOtraMoneda,
  td.monto1 AS MontoItem,
  p.NotaImpresion
FROM
  dbo.tradetalle AS td WITH (NOLOCK)
  LEFT OUTER JOIN dbo.cxcmovi1 AS cxc WITH (NOLOCK) ON cxc.documento = td.numero AND cxc.tipomovi= '03' and td.tipo = '05'
  LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
  LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON trim(cxc.RNCEmisor) = trim(e.rnc)
  
WHERE
  (td.tipo IN ('05'))
  --and   td.numero = 'A00000000351'

GO
/****** Object:  View [dbo].[vFEDevCODetRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFEDevCODetRD] as
WITH
  e AS (  SELECT itbisenprecio, rnc FROM empresa WITH (NOLOCK)   )

SELECT
  td.orden AS NumeroLinea,
  td.numero AS NumeroFacturaInterna,
  td.tipo AS TipoDocumento,
  SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
  SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
  tr.ncf AS eNCF,
  tr.RNCEmisor,
  CAST('Interna' AS CHAR(100)) AS TipoCodigo1,
  CAST(td.producto AS CHAR(100)) AS CodigoItem1,
  CAST('' AS CHAR(100)) AS TipoCodigo2,
  CAST('' AS CHAR(100)) AS CodigoItem2,
  CAST('' AS CHAR(100)) AS TipoCodigo3,
  CAST('' AS CHAR(100)) AS CodigoItem3,
  CAST('' AS CHAR(100)) AS TipoCodigo4,
  CAST('' AS CHAR(100)) AS CodigoItem4,
  CAST('' AS CHAR(100)) AS TipoCodigo5,
  CAST('' AS CHAR(100)) AS CodigoItem5,
  i.codigodgii AS IndicadorFacturacion,
  i.Siglas AS SiglasImpuesto,
  i.Descrip AS DescripcionImpuesto,
  NULL AS IndicadorAgenteRetencionoPercepcion,
  NULL AS MontoITBISRetenido,
  NULL AS MontoISRRetenido,
  TRIM(p.descrip) AS NombreItem,
  CASE
    p.servicio
    WHEN 0 THEN 1
    WHEN 1 THEN 2
    ELSE 1
  END AS IndicadorBienoServicio,
  NULL AS DescripcionItem,
  CASE
    WHEN td.cantidad < 0 THEN td.cantidad * - 1
    ELSE td.cantidad
  END AS CantidadItem,
  '' AS UnidadMedida,
  '' as UnidadMedidaL,
  NULL AS CantidadReferencia,
  NULL AS UnidadReferencia,
  NULL AS Subcantidad1,
  NULL AS CodigoSubcantidad1,
  NULL AS Subcantidad2,
  NULL AS CodigoSubcantidad2,
  NULL AS Subcantidad3,
  NULL AS CodigoSubcantidad3,
  NULL AS Subcantidad4,
  NULL AS CodigoSubcantidad4,
  NULL AS Subcantidad5,
  NULL AS CodigoSubcantidad5,
  NULL AS GradosAlcohol,
  NULL AS PrecioUnitarioReferencia,
  NULL AS FechaElaboracion,
  NULL AS FechaVencimientoItem,
  NULL AS PesoNetoKilogramo,
  NULL AS PesoNetoMineria,
  NULL AS TipoAfiliacion,
  NULL AS Liquidacion,
  td.precio  AS PrecioUnitarioItem,
  td.montodesc  AS DescuentoMonto,
  td.itbis AS TasaITBIS,
  e.itbisenprecio AS IndicadorMontoGravado,
  
  td.montoitbis  AS MontoITBIS,

  td.descuen AS TasaDescuento,
  '$' AS TipoSubDescuento1,
  null AS SubDescuentoPorcentaje1,
  td.montodesc AS MontoSubDescuento1,
  NULL AS TipoSubDescuento2,
  NULL AS SubDescuentoPorcentaje2,
  NULL AS MontoSubDescuento2,
  NULL AS TipoSubDescuento3,
  NULL AS SubDescuentoPorcentaje3,
  NULL AS MontoSubDescuento3,
  NULL AS TipoSubDescuento4,
  NULL AS SubDescuentoPorcentaje4,
  NULL AS MontoSubDescuento4,
  NULL AS TipoSubDescuento5,
  NULL AS SubDescuentoPorcentaje5,
  NULL AS MontoSubDescuento5,
  NULL AS MontoRecargo,
  NULL AS TipoSubRecargo1,
  NULL AS SubRecargoPorcentaje1,
  NULL AS MontoSubRecargo1,
  NULL AS TipoSubRecargo2,
  NULL AS SubRecargoPorcentaje2,
  NULL AS MontoSubRecargo2,
  NULL AS TipoSubRecargo3,
  NULL AS SubRecargoPorcentaje3,
  NULL AS MontoSubRecargo3,
  NULL AS TipoSubRecargo4,
  NULL AS SubRecargoPorcentaje4,
  NULL AS MontoSubRecargo4,
  NULL AS TipoSubRecargo5,
  NULL AS SubRecargoPorcentaje5,
  NULL AS MontoSubRecargo5,
  NULL AS TipoImpuesto1,
  NULL AS TipoImpuesto2,
  COALESCE(tr.tasa,1) AS TipoCambio,
  null AS MontoITBISOtraMoneda,
  null AS PrecioOtraMoneda,
  null AS DescuentoOtraMoneda,
  NULL AS MontoRecargoOtraMoneta,
  null AS MontoItemOtraMoneda,
  td.monto1 AS MontoItem,
  p.NotaImpresion
FROM
  dbo.tradetalle AS td WITH (NOLOCK)
  LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
  LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor = e.rnc
  
WHERE
  (td.tipo IN ('17'))
  AND (tr.EstadoFiscal IS NOT NULL) 
  AND COALESCE(tr.tasa, 1)= 1


GO
/****** Object:  View [dbo].[vFEVentaDetRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFEVentaDetRD] as
WITH
  e AS (  SELECT itbisenprecio, rnc FROM empresa WITH (NOLOCK)   )

SELECT
  td.orden AS NumeroLinea,
  td.numero AS NumeroFacturaInterna,
  td.tipo AS TipoDocumento,
  SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
  SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
  tr.ncf AS eNCF,
  tr.RNCEmisor,
  CAST('Interna' AS CHAR(100)) AS TipoCodigo1,
  RIGHT(trim(td.producto), 4)  AS CodigoItem1,
  CAST('' AS CHAR(100)) AS TipoCodigo2,
  CAST('' AS CHAR(100)) AS CodigoItem2,
  CAST('' AS CHAR(100)) AS TipoCodigo3,
  CAST('' AS CHAR(100)) AS CodigoItem3,
  CAST('' AS CHAR(100)) AS TipoCodigo4,
  CAST('' AS CHAR(100)) AS CodigoItem4,
  CAST('' AS CHAR(100)) AS TipoCodigo5,
  CAST('' AS CHAR(100)) AS CodigoItem5,
  i.codigodgii AS IndicadorFacturacion,
  i.Siglas AS SiglasImpuesto,
  i.Descrip AS DescripcionImpuesto,
  NULL AS IndicadorAgenteRetencionoPercepcion,
  NULL AS MontoITBISRetenido,
  NULL AS MontoISRRetenido,
  left(TRIM(p.descrip),35) AS NombreItem,
  CASE
    p.servicio
    WHEN 0 THEN 1
    WHEN 1 THEN 2
    ELSE 1
  END AS IndicadorBienoServicio,
  NULL AS DescripcionItem,
  CASE
    WHEN td.cantidad2 < 0 THEN td.cantidad2 * - 1
    ELSE td.cantidad2
  END AS CantidadItem,
  '' AS UnidadMedida,
  u.descrip as UnidadMedidaL,
  NULL AS CantidadReferencia,
  NULL AS UnidadReferencia,
  NULL AS Subcantidad1,
  NULL AS CodigoSubcantidad1,
  NULL AS Subcantidad2,
  NULL AS CodigoSubcantidad2,
  NULL AS Subcantidad3,
  NULL AS CodigoSubcantidad3,
  NULL AS Subcantidad4,
  NULL AS CodigoSubcantidad4,
  NULL AS Subcantidad5,
  NULL AS CodigoSubcantidad5,
  NULL AS GradosAlcohol,
  NULL AS PrecioUnitarioReferencia,
  NULL AS FechaElaboracion,
  NULL AS FechaVencimientoItem,
  NULL AS PesoNetoKilogramo,
  NULL AS PesoNetoMineria,
  NULL AS TipoAfiliacion,
  NULL AS Liquidacion,
  td.precio  AS PrecioUnitarioItem,
  td.montodesc  AS DescuentoMonto,
  td.itbis AS TasaITBIS,
  e.itbisenprecio AS IndicadorMontoGravado,
  
  td.montoitbis  AS MontoITBIS,

  td.descuen AS TasaDescuento,
  '$' AS TipoSubDescuento1,
  NULL AS SubDescuentoPorcentaje1,
  td.montodesc AS MontoSubDescuento1,
  NULL AS TipoSubDescuento2,
  NULL AS SubDescuentoPorcentaje2,
  NULL AS MontoSubDescuento2,
  NULL AS TipoSubDescuento3,
  NULL AS SubDescuentoPorcentaje3,
  NULL AS MontoSubDescuento3,
  NULL AS TipoSubDescuento4,
  NULL AS SubDescuentoPorcentaje4,
  NULL AS MontoSubDescuento4,
  NULL AS TipoSubDescuento5,
  NULL AS SubDescuentoPorcentaje5,
  NULL AS MontoSubDescuento5,
  NULL AS MontoRecargo,
  NULL AS TipoSubRecargo1,
  NULL AS SubRecargoPorcentaje1,
  NULL AS MontoSubRecargo1,
  NULL AS TipoSubRecargo2,
  NULL AS SubRecargoPorcentaje2,
  NULL AS MontoSubRecargo2,
  NULL AS TipoSubRecargo3,
  NULL AS SubRecargoPorcentaje3,
  NULL AS MontoSubRecargo3,
  NULL AS TipoSubRecargo4,
  NULL AS SubRecargoPorcentaje4,
  NULL AS MontoSubRecargo4,
  NULL AS TipoSubRecargo5,
  NULL AS SubRecargoPorcentaje5,
  NULL AS MontoSubRecargo5,
  NULL AS TipoImpuesto1,
  NULL AS TipoImpuesto2,
  COALESCE(tr.tasa,1) AS TipoCambio,
  null AS MontoITBISOtraMoneda,
  null AS PrecioOtraMoneda,
  null AS DescuentoOtraMoneda,
  NULL AS MontoRecargoOtraMoneta,
  null AS MontoItemOtraMoneda,
  td.monto1-td.montodesc AS MontoItem,
  p.NotaImpresion
FROM
  dbo.tradetalle AS td WITH (NOLOCK)
  LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
  LEFT OUTER JOIN dbo.unidad AS u WITH (NOLOCK) ON u.unidad = td.unidad2
  LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor = e.rnc
  
WHERE
  (td.tipo IN ('03', '04'))
  AND (tr.EstadoFiscal IS NOT NULL) 
  AND td.precio >=0
GO
/****** Object:  View [dbo].[vFEVentaDetUS]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFEVentaDetUS] as
WITH
  e AS (  SELECT itbisenprecio, rnc FROM empresa WITH (NOLOCK)   )

SELECT
  td.orden AS NumeroLinea,
  td.numero AS NumeroFacturaInterna,
  td.tipo AS TipoDocumento,
  SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
  SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
  tr.ncf AS eNCF,
  tr.RNCEmisor,
  CAST('Interna' AS CHAR(100)) AS TipoCodigo1,
  CAST(td.producto AS CHAR(100)) AS CodigoItem1,
  CAST('' AS CHAR(100)) AS TipoCodigo2,
  CAST('' AS CHAR(100)) AS CodigoItem2,
  CAST('' AS CHAR(100)) AS TipoCodigo3,
  CAST('' AS CHAR(100)) AS CodigoItem3,
  CAST('' AS CHAR(100)) AS TipoCodigo4,
  CAST('' AS CHAR(100)) AS CodigoItem4,
  CAST('' AS CHAR(100)) AS TipoCodigo5,
  CAST('' AS CHAR(100)) AS CodigoItem5,
  i.codigodgii AS IndicadorFacturacion,
  i.Siglas AS SiglasImpuesto,
  i.Descrip AS DescripcionImpuesto,
  NULL AS IndicadorAgenteRetencionoPercepcion,
  NULL AS MontoITBISRetenido,
  NULL AS MontoISRRetenido,
  TRIM(p.descrip) AS NombreItem,
  CASE
    p.servicio
    WHEN 0 THEN 1
    WHEN 1 THEN 2
    ELSE 1
  END AS IndicadorBienoServicio,
  NULL AS DescripcionItem,
  CASE
    WHEN td.cantidad2 < 0 THEN td.cantidad2 * - 1
    ELSE td.cantidad2
  END AS CantidadItem,
  '' AS UnidadMedida,
  u.descrip as UnidadMedidaL,
  NULL AS CantidadReferencia,
  NULL AS UnidadReferencia,
  NULL AS Subcantidad1,
  NULL AS CodigoSubcantidad1,
  NULL AS Subcantidad2,
  NULL AS CodigoSubcantidad2,
  NULL AS Subcantidad3,
  NULL AS CodigoSubcantidad3,
  NULL AS Subcantidad4,
  NULL AS CodigoSubcantidad4,
  NULL AS Subcantidad5,
  NULL AS CodigoSubcantidad5,
  NULL AS GradosAlcohol,
  NULL AS PrecioUnitarioReferencia,
  NULL AS FechaElaboracion,
  NULL AS FechaVencimientoItem,
  NULL AS PesoNetoKilogramo,
  NULL AS PesoNetoMineria,
  NULL AS TipoAfiliacion,
  NULL AS Liquidacion,
  (
    CASE
      WHEN COALESCE(tr.tasa, 1) = 1 THEN td.precio * 1
      ELSE td.precio * tr.tasa
    END
  ) AS PrecioUnitarioItem,

  (
    CASE
      WHEN COALESCE(tr.tasa, 1) = 1 THEN td.montodesc * 1
      ELSE td.montodesc * tr.tasa
    END
  ) AS DescuentoMonto,
  td.itbis AS TasaITBIS,
  e.itbisenprecio AS IndicadorMontoGravado,
  
  (
    CASE
      WHEN COALESCE(tr.tasa, 1) = 1 THEN td.montoitbis * 1
      ELSE td.montoitbis * tr.tasa
    END
  ) AS MontoITBIS,

  td.descuen AS TasaDescuento,
  '%' AS TipoSubDescuento1,
  td.descuen AS SubDescuentoPorcentaje1,
 td.montodesc AS MontoSubDescuento1,
  NULL AS TipoSubDescuento2,
  NULL AS SubDescuentoPorcentaje2,
  NULL AS MontoSubDescuento2,
  NULL AS TipoSubDescuento3,
  NULL AS SubDescuentoPorcentaje3,
  NULL AS MontoSubDescuento3,
  NULL AS TipoSubDescuento4,
  NULL AS SubDescuentoPorcentaje4,
  NULL AS MontoSubDescuento4,
  NULL AS TipoSubDescuento5,
  NULL AS SubDescuentoPorcentaje5,
  NULL AS MontoSubDescuento5,
  NULL AS MontoRecargo,
  NULL AS TipoSubRecargo1,
  NULL AS SubRecargoPorcentaje1,
  NULL AS MontoSubRecargo1,
  NULL AS TipoSubRecargo2,
  NULL AS SubRecargoPorcentaje2,
  NULL AS MontoSubRecargo2,
  NULL AS TipoSubRecargo3,
  NULL AS SubRecargoPorcentaje3,
  NULL AS MontoSubRecargo3,
  NULL AS TipoSubRecargo4,
  NULL AS SubRecargoPorcentaje4,
  NULL AS MontoSubRecargo4,
  NULL AS TipoSubRecargo5,
  NULL AS SubRecargoPorcentaje5,
  NULL AS MontoSubRecargo5,
  NULL AS TipoImpuesto1,
  NULL AS TipoImpuesto2,
  COALESCE(tr.tasa, 1) AS TipoCambio,
  td.montoitbis AS MontoITBISOtraMoneda,
  td.precio AS PrecioOtraMoneda,
  td.montodesc AS DescuentoOtraMoneda,
  NULL AS MontoRecargoOtraMoneta,
  td.monto1 AS MontoItemOtraMoneda,
  
  (
    CASE
      WHEN COALESCE(tr.tasa, 1) = 1 THEN td.monto1 * 1
      ELSE td.monto1 * COALESCE(tr.tasa, 1)
    END
  ) AS MontoItem,

 
 


 
  p.NotaImpresion
FROM
  dbo.tradetalle AS td
  LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
  LEFT OUTER JOIN dbo.unidad AS u WITH (NOLOCK) ON u.unidad = td.unidad2  
  LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor = e.rnc
WHERE
  (td.tipo IN ('33', '34'))
  AND (tr.EstadoFiscal IS NOT NULL) 

GO
/****** Object:  View [dbo].[vFEDetGASMENCC]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFEDetGASMENCC] as

SELECT 

    NULL AS NumeroLinea,
    max(cc.documento) AS NumeroFacturaInterna,
    max(cc.ncftipo) AS TipoDocumento,
    max(SUBSTRING (cc.ncf, 2, 2)) AS TipoECF,
    max(SUBSTRING (cc.ncf, 1, 1)) AS TipoECFL,
	cc.ncf as eNCF,
	cc.RNCEmisor,
    CAST('Interno' AS CHAR(100)) AS TipoCodigo1,
    CAST(max(cc.cuenta) AS CHAR(100)) AS CodigoItem1,
    CAST('' AS CHAR(100)) AS TipoCodigo2,
    CAST('' AS CHAR(100)) AS CodigoItem2,
    CAST('' AS CHAR(100)) AS TipoCodigo3,
    CAST('' AS CHAR(100)) AS CodigoItem3,
    CAST('' AS CHAR(100)) AS TipoCodigo4,
    CAST('' AS CHAR(100)) AS CodigoItem4,
    CAST('' AS CHAR(100)) AS TipoCodigo5,
    CAST('' AS CHAR(100)) AS CodigoItem5,
    4 AS IndicadorFacturacion,
    max(i.Siglas) AS SiglasImpuesto,
    max(i.Descrip) AS DescripcionImpuesto,
    NULL AS IndicadorAgenteRetencionoPercepcion,
    NULL AS MontoITBISRetenido,
    NULL AS MontoISRRetenido,
    max(cc.DESCRIP) NombreItem,
    1 AS IndicadorBienoServicio,
    NULL AS DescripcionItem,
    1 AS CantidadItem,
    '' AS UnidadMedida,
    '' as UnidadMedidaL,
    NULL AS CantidadReferencia,
    NULL AS UnidadReferencia,
    NULL AS Subcantidad1,
    NULL AS CodigoSubcantidad1,
    NULL AS Subcantidad2,
    NULL AS CodigoSubcantidad2,
    NULL AS Subcantidad3,
    NULL AS CodigoSubcantidad3,
    NULL AS Subcantidad4,
    NULL AS CodigoSubcantidad4,
    NULL AS Subcantidad5,
    NULL AS CodigoSubcantidad5,
    NULL AS GradosAlcohol,
    NULL AS PrecioUnitarioReferencia,
    NULL AS FechaElaboracion,
    NULL AS FechaVencimientoItem,
    NULL AS PesoNetoKilogramo,
    NULL AS PesoNetoMineria,
    NULL AS TipoAfiliacion,
    NULL AS Liquidacion,
    SUM(cc.debito - cc.credito) AS PrecioUnitarioItem,
    NULL AS DescuentoMonto,
    0 AS TasaITBIS,
    1 AS IndicadorMontoGravado,
    NULL AS MontoITBIS,
    NULL AS TasaDescuento,
    '' AS TipoSubDescuento1,
    NULL AS SubDescuentoPorcentaje1,
    NULL AS MontoSubDescuento1,
    NULL AS TipoSubDescuento2,
    NULL AS SubDescuentoPorcentaje2,
    NULL AS MontoSubDescuento2,
    NULL AS TipoSubDescuento3,
    NULL AS SubDescuentoPorcentaje3,
    NULL AS MontoSubDescuento3,
    NULL AS TipoSubDescuento4,
    NULL AS SubDescuentoPorcentaje4,
    NULL AS MontoSubDescuento4,
    NULL AS TipoSubDescuento5,
    NULL AS SubDescuentoPorcentaje5,
    NULL AS MontoSubDescuento5,
    NULL AS MontoRecargo,
    NULL AS TipoSubRecargo1,
    NULL AS SubRecargoPorcentaje1,
    NULL AS MontoSubRecargo1,
    NULL AS TipoSubRecargo2,
    NULL AS SubRecargoPorcentaje2,
    NULL AS MontoSubRecargo2,
    NULL AS TipoSubRecargo3,
    NULL AS SubRecargoPorcentaje3,
    NULL AS MontoSubRecargo3,
    NULL AS TipoSubRecargo4,
    NULL AS SubRecargoPorcentaje4,
    NULL AS MontoSubRecargo4,
    NULL AS TipoSubRecargo5,
    NULL AS SubRecargoPorcentaje5,
    NULL AS MontoSubRecargo5,
    NULL AS TipoImpuesto1,
    NULL AS TipoImpuesto2,
    1 AS TipoCambio,
    NULL AS MontoITBISOtraMoneda,
    NULL AS PrecioOtraMoneda,
    NULL AS DescuentoOtraMoneda,
    NULL AS MontoRecargoOtraMoneta,
    NULL AS MontoItemOtraMoneda,
    SUM(cc.debito - cc.credito) AS MontoItem,
	'' AS NotaImpresion
FROM cajachica cc
LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = '00'
WHERE cc.ncftipo IN ('GM') 
    AND (cc.ncf IS NOT NULL) 
    AND (cc.ncf <> '') 
    AND (cc.EstadoFiscal IS NOT NULL)
    AND SUBSTRING(cc.ncf, 1, 1) = 'E'
    AND cc.RNCEmisor IS NOT NULL
GROUP BY 
    cc.RNCEmisor,
    cc.ncf
GO
/****** Object:  View [dbo].[vFEDetGASMENCXP]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     VIEW   [dbo].[vFEDetGASMENCXP] as

SELECT 

    NULL AS NumeroLinea,
    cxp.documento AS NumeroFacturaInterna,
    cxp.ncf AS TipoDocumento,
    SUBSTRING (cxp.ncf, 2, 2) AS TipoECF,
    SUBSTRING (cxp.ncf, 1, 1) AS TipoECFL,
	cxp.ncf as eNCF,
	cxp.RNCEmisor,
    'Interno'  AS TipoCodigo1,
    trim(cxp.documento) AS CodigoItem1,
    CAST('' AS CHAR(100)) AS TipoCodigo2,
    CAST('' AS CHAR(100)) AS CodigoItem2,
    CAST('' AS CHAR(100)) AS TipoCodigo3,
    CAST('' AS CHAR(100)) AS CodigoItem3,
    CAST('' AS CHAR(100)) AS TipoCodigo4,
    CAST('' AS CHAR(100)) AS CodigoItem4,
    CAST('' AS CHAR(100)) AS TipoCodigo5,
    CAST('' AS CHAR(100)) AS CodigoItem5,
    4 AS IndicadorFacturacion,
    'E' AS SiglasImpuesto,
    i.Descrip AS DescripcionImpuesto,
    NULL AS IndicadorAgenteRetencionoPercepcion,
    NULL AS MontoITBISRetenido,
    NULL AS MontoISRRetenido,
    cxp.CONCEPTO NombreItem,
    1 AS IndicadorBienoServicio,
    NULL AS DescripcionItem,
    1 AS CantidadItem,
    '' AS UnidadMedida,
    '' as UnidadMedidaL,
    NULL AS CantidadReferencia,
    NULL AS UnidadReferencia,
    NULL AS Subcantidad1,
    NULL AS CodigoSubcantidad1,
    NULL AS Subcantidad2,
    NULL AS CodigoSubcantidad2,
    NULL AS Subcantidad3,
    NULL AS CodigoSubcantidad3,
    NULL AS Subcantidad4,
    NULL AS CodigoSubcantidad4,
    NULL AS Subcantidad5,
    NULL AS CodigoSubcantidad5,
    NULL AS GradosAlcohol,
    NULL AS PrecioUnitarioReferencia,
    NULL AS FechaElaboracion,
    NULL AS FechaVencimientoItem,
    NULL AS PesoNetoKilogramo,
    NULL AS PesoNetoMineria,
    NULL AS TipoAfiliacion,
    NULL AS Liquidacion,
    cxp.monto AS PrecioUnitarioItem,
    NULL AS DescuentoMonto,
    0 AS TasaITBIS,
    1 AS IndicadorMontoGravado,
    NULL AS MontoITBIS,
    NULL AS TasaDescuento,
    '' AS TipoSubDescuento1,
    NULL AS SubDescuentoPorcentaje1,
    NULL AS MontoSubDescuento1,
    NULL AS TipoSubDescuento2,
    NULL AS SubDescuentoPorcentaje2,
    NULL AS MontoSubDescuento2,
    NULL AS TipoSubDescuento3,
    NULL AS SubDescuentoPorcentaje3,
    NULL AS MontoSubDescuento3,
    NULL AS TipoSubDescuento4,
    NULL AS SubDescuentoPorcentaje4,
    NULL AS MontoSubDescuento4,
    NULL AS TipoSubDescuento5,
    NULL AS SubDescuentoPorcentaje5,
    NULL AS MontoSubDescuento5,
    NULL AS MontoRecargo,
    NULL AS TipoSubRecargo1,
    NULL AS SubRecargoPorcentaje1,
    NULL AS MontoSubRecargo1,
    NULL AS TipoSubRecargo2,
    NULL AS SubRecargoPorcentaje2,
    NULL AS MontoSubRecargo2,
    NULL AS TipoSubRecargo3,
    NULL AS SubRecargoPorcentaje3,
    NULL AS MontoSubRecargo3,
    NULL AS TipoSubRecargo4,
    NULL AS SubRecargoPorcentaje4,
    NULL AS MontoSubRecargo4,
    NULL AS TipoSubRecargo5,
    NULL AS SubRecargoPorcentaje5,
    NULL AS MontoSubRecargo5,
    NULL AS TipoImpuesto1,
    NULL AS TipoImpuesto2,
    1 AS TipoCambio,
    NULL AS MontoITBISOtraMoneda,
    NULL AS PrecioOtraMoneda,
    NULL AS DescuentoOtraMoneda,
    NULL AS MontoRecargoOtraMoneta,
    NULL AS MontoItemOtraMoneda,
    cxp.monto AS MontoItem,
	'' AS NotaImpresion
FROM cxpmovi1 cxp
LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = '00'
WHERE
  cxp.tipoMOVI IN ('07')
  AND cxp.gmenor = 1
  AND cxp.ncf IS NOT NULL
  AND cxp.ncf <> ''
  AND cxp.EstadoFiscal IS NOT NULL
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND cxp.RNCEmisor IS NOT NULL


    /*
  Select * from cxpmovi1 cxp

  WHERE
  cxp.tipoMOVI IN ('07')
  AND cxp.gmenor = 1
  AND cxp.ncf IS NOT NULL
  AND cxp.ncf <> ''
  AND cxp.EstadoFiscal IS NOT NULL
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND cxp.RNCEmisor IS NOT NULL

  */


GO
/****** Object:  View [dbo].[vFEDetalle]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO



CREATE   view [dbo].[vFEDetalle] as

Select * from vFEVentaDetRD

union all

Select * from vFEVentaDetUS

union all

Select * from vFEDevCODetRD

union all

Select * from vFEDevCRDetRD

union all

Select * from vFENCDIDEtRD

Union all

--Gastos Menores
Select * from vFEDetGASMENCXP

Union all

Select * from vFEDetGASMENCC

Union All

-- Proveedores Informales
Select * from vFEDetPI

GO
/****** Object:  View [dbo].[ConsultaSubDescuentoRecargo]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[ConsultaSubDescuentoRecargo]
AS
SELECT        t.ID, t.Documento, t.producto, t.linea, t.Tipo, t.TipoSubDescuentoRecargo, t.MontoSubDescuentoRecargo, d.itbis
FROM            dbo.SubDescuentoRecargo AS t INNER JOIN
                         dbo.tradetalle AS d ON d.documento = t.Documento AND t.producto = d.producto AND t.linea = d.orden
GO
/****** Object:  View [dbo].[vConsultaDescuentoRecargos]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[vConsultaDescuentoRecargos]
AS
SELECT NumeroLinea, TipoAjuste, IndicadorNorma1007, DescripcionDesRec, TipoValor, MontoDescuentoRecargo, MontoDescuentoRecargoOtraModena, IndicadorFacturacionDescuentoRecargo, Documento, ValorDescuentoRecargo
FROM   dbo.DescuentoRecargos
GO
/****** Object:  View [dbo].[vConsultaDetalleFactura]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[vConsultaDetalleFactura]
AS
SELECT t.numero AS documento, t.producto, p.descrip, CASE WHEN t .cantidad < 0 THEN t .cantidad * - 1 ELSE t .cantidad END AS cantidad, t.precio, t.monto1, t.itbis, t.montoitbis, t.descuen, t.orden, t.montodesc, '' AS refe, t.ordenp, u.unidad AS suma, 0 AS costo1us, 0 AS credito, '' AS PrecioUnitarioReferencia, '' AS GradosAlcohol, 
           '' AS CodigoSubCantidad, '' AS SubCantidad, '' AS TipoImpuesto1, '' AS TipoImpuesto2, '' AS TasaImpuestoAdicional1, '' AS TasaImpuestoAdicional2, '' AS MontoImpuestoSelectivoConsumoEspe1, '' AS MontoImpuestoSelectivoConsumoEspe2, '' AS MontoImpuestoSelectivoConsumoAdvrem, 1 AS BienServicio, 
           '' AS OtroImpuestosAdicionales1, '' AS OtroImpuestosAdicionales2, '' AS TipoSubRecargo, '' AS MontoSubRecargo, '' AS TipoCodigo, t.producto AS CodigoItem, p.descrip AS DescripcionItem, t.costo2, t.costo1, '' AS empresa, t.tasa, u.descrip AS abreviatura, u.cantidad AS medida, ti.TipoItbis AS IndicadorFactura, '' AS ncf, t.tipo as TipoFactura
FROM   dbo.tradetalle AS t INNER JOIN
           dbo.producto AS p ON p.producto = t.producto LEFT OUTER JOIN
           dbo.unidad AS u ON CAST(u.unidad AS int) = CAST(t.unidad2 AS int) LEFT OUTER JOIN
           dbo.TipoItbis AS ti ON ti.Valor = t.itbis
WHERE (t.tipo IN ('03', '04'))
GO
/****** Object:  View [dbo].[vConsultaDetalleGastoMenor]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[vConsultaDetalleGastoMenor]
AS
SELECT 43 AS TipoeCF, '01' AS TipoIngresos, 2 AS TipoPago, DATEADD(day, 30, GETDATE()) AS FechaLimitePago, 0 AS TerminoPago, GETDATE() AS FechaEmision, REPLACE(trim(c.rnc), '-', '') AS RNCComprador, LEFT(trim(c.BENeFICIARIO), 150) AS RazonSocialComprador, m.monto AS MontoGravadoTotal, 0 AS TotalDescuento, 
           ISNULL(i.itbis, 0) AS TotalITBIS, m.monto AS MontoTotal, 'DOP' AS TipoMoneda, c.TRANSA AS documento
FROM   dbo.CAJACHICA AS c INNER JOIN
               (SELECT TRANSA, SUM(DEBITO) AS monto
              FROM   dbo.CAJACHICA AS cs
              GROUP BY TRANSA) AS m ON m.TRANSA = c.TRANSA LEFT OUTER JOIN
               (SELECT TRANSA, SUM(DEBITO) AS itbis
              FROM   dbo.CAJACHICA AS ca
              WHERE (CUENTA = '114-01-11')
              GROUP BY TRANSA) AS i ON i.TRANSA = c.TRANSA
WHERE (c.ncftipo = 'GM')
GO
/****** Object:  View [dbo].[VConsultaFactura]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[VConsultaFactura]
AS
SELECT t.documento,t.tipo AS TipoFactura, SUBSTRING(t.ncf, 2, 2) AS TipoeCF, f.descripcion AS NCFNombre, '01' AS TipoIngresos, 7 AS TipoPago, t.vence AS FechaLimitePago, t.dia AS TerminoPago, t.fecha AS FechaEmision, REPLACE(trim(t.cedula), '-', '') AS RNCComprador, LEFT(trim(t.nombre), 150) AS RazonSocialComprador, 
           t.nograva AS MontoGravadoTotal, t.descuen AS TotalDescuento, t.itbis AS TotalITBIS, t.monto AS MontoTotal, 'DOP' AS TipoMoneda,  '' AS zonaname, t.ciudad, t.dire, t.otros, t.flete, t.grava, t.balance, t.total, '' AS RazonModificacion, '' AS CodigoModificacion, t.fecha AS FechaNCFModificado, t.ncf1 AS NCFModificado, 
           1 AS FormaPago, '' AS IndicadorNotaCredito, t.venname AS ContactoComprador, t.fecha AS FechaEntrega, '' AS NumeroPedidoInterno, t.numero AS NumeroFacturaInterna, t.vendedor AS CodigoVendedor, '' AS CodigoInternoComprador, t.creado, t.observa, t.pedido, t.descrip1, t.descrip2, '' AS documentoliq, '' AS datecontrol, 
           '' AS IdentificadorExtranjero, t.ncf, t.fVencimientoNCF
FROM   dbo.Transa01 AS t LEFT OUTER JOIN
           dbo.ferd_TipoNCF AS f ON f.codigo = SUBSTRING(t.ncf, 2, 2) COLLATE Modern_Spanish_CI_AS
WHERE (t.tipo IN ('03', '04'))
GO
/****** Object:  View [dbo].[vFEDetGASMEN]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFEDetGASMEN] as

SELECT 

    NULL AS NumeroLinea,
    max(cc.documento) AS NumeroFacturaInterna,
    max(cc.ncftipo) AS TipoDocumento,
    max(SUBSTRING (cc.ncf, 2, 2)) AS TipoECF,
    max(SUBSTRING (cc.ncf, 1, 1)) AS TipoECFL,
	cc.ncf as eNCF,
	cc.RNCEmisor,
    CAST('Interno' AS CHAR(100)) AS TipoCodigo1,
    CAST(max(cc.cuenta) AS CHAR(100)) AS CodigoItem1,
    CAST('' AS CHAR(100)) AS TipoCodigo2,
    CAST('' AS CHAR(100)) AS CodigoItem2,
    CAST('' AS CHAR(100)) AS TipoCodigo3,
    CAST('' AS CHAR(100)) AS CodigoItem3,
    CAST('' AS CHAR(100)) AS TipoCodigo4,
    CAST('' AS CHAR(100)) AS CodigoItem4,
    CAST('' AS CHAR(100)) AS TipoCodigo5,
    CAST('' AS CHAR(100)) AS CodigoItem5,
    4 AS IndicadorFacturacion,
    max(i.Siglas) AS SiglasImpuesto,
    max(i.Descrip) AS DescripcionImpuesto,
    NULL AS IndicadorAgenteRetencionoPercepcion,
    NULL AS MontoITBISRetenido,
    NULL AS MontoISRRetenido,
    max(cc.DESCRIP) NombreItem,
    1 AS IndicadorBienoServicio,
    NULL AS DescripcionItem,
    1 AS CantidadItem,
    null AS UnidadMedida,
    null as UnidadMedidaL,
    NULL AS CantidadReferencia,
    NULL AS UnidadReferencia,
    NULL AS Subcantidad1,
    NULL AS CodigoSubcantidad1,
    NULL AS Subcantidad2,
    NULL AS CodigoSubcantidad2,
    NULL AS Subcantidad3,
    NULL AS CodigoSubcantidad3,
    NULL AS Subcantidad4,
    NULL AS CodigoSubcantidad4,
    NULL AS Subcantidad5,
    NULL AS CodigoSubcantidad5,
    NULL AS GradosAlcohol,
    NULL AS PrecioUnitarioReferencia,
    NULL AS FechaElaboracion,
    NULL AS FechaVencimientoItem,
    NULL AS PesoNetoKilogramo,
    NULL AS PesoNetoMineria,
    NULL AS TipoAfiliacion,
    NULL AS Liquidacion,
    SUM(cc.debito - cc.credito) AS PrecioUnitarioItem,
    NULL AS DescuentoMonto,
    0 AS TasaITBIS,
    1 AS IndicadorMontoGravado,
    NULL AS MontoITBIS,
    NULL AS TasaDescuento,
    '' AS TipoSubDescuento1,
    NULL AS SubDescuentoPorcentaje1,
    NULL AS MontoSubDescuento1,
    NULL AS TipoSubDescuento2,
    NULL AS SubDescuentoPorcentaje2,
    NULL AS MontoSubDescuento2,
    NULL AS TipoSubDescuento3,
    NULL AS SubDescuentoPorcentaje3,
    NULL AS MontoSubDescuento3,
    NULL AS TipoSubDescuento4,
    NULL AS SubDescuentoPorcentaje4,
    NULL AS MontoSubDescuento4,
    NULL AS TipoSubDescuento5,
    NULL AS SubDescuentoPorcentaje5,
    NULL AS MontoSubDescuento5,
    NULL AS MontoRecargo,
    NULL AS TipoSubRecargo1,
    NULL AS SubRecargoPorcentaje1,
    NULL AS MontoSubRecargo1,
    NULL AS TipoSubRecargo2,
    NULL AS SubRecargoPorcentaje2,
    NULL AS MontoSubRecargo2,
    NULL AS TipoSubRecargo3,
    NULL AS SubRecargoPorcentaje3,
    NULL AS MontoSubRecargo3,
    NULL AS TipoSubRecargo4,
    NULL AS SubRecargoPorcentaje4,
    NULL AS MontoSubRecargo4,
    NULL AS TipoSubRecargo5,
    NULL AS SubRecargoPorcentaje5,
    NULL AS MontoSubRecargo5,
    NULL AS TipoImpuesto1,
    NULL AS TipoImpuesto2,
    1 AS TipoCambio,
    NULL AS MontoITBISOtraMoneda,
    NULL AS PrecioOtraMoneda,
    NULL AS DescuentoOtraMoneda,
    NULL AS MontoRecargoOtraMoneta,
    NULL AS MontoItemOtraMoneda,
    SUM(cc.debito - cc.credito) AS MontoItem,
	'' AS NotaImpresion
FROM cajachica cc
LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = '00'
WHERE cc.ncftipo IN ('GM') 
    AND (cc.ncf IS NOT NULL) 
    AND (cc.ncf <> '') 
    AND (cc.EstadoFiscal IS NOT NULL)
GROUP BY 
    cc.RNCEmisor,
    cc.ncf



GO
/****** Object:  View [dbo].[vFEDevCOCRRD]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFEDevCOCRRD] AS 
--Nota de credito por devolucion 
--Movimiento 05
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
),

Totales AS (

	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))
		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
)
 --Datos de Tradetalle
 --Datos de las tablas para construir las NC
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
  tr.fecha AS FechaLimitePago, -- Debe ser la misma fecha de Emision en el caso de las NC
  0 AS TerminoPagoN,
  '' AS  TerminoPago,
  tr.almacen AS Almacen,
    (
	CASE
      WHEN DATEDIFF(DAY, tr1.fecha, tr.fecha) >30 THEN 1
	  ELSE 0
    END
  ) AS IndicadorNotaCredito,
  e.itbisenprecio AS IndicadorMontoGravado,
  '01' AS TipoIngresos,
  1 AS TipoPago,  -- Hay qeu poner que tome el tipo de la factura (a credito  oa contado)
 'CONTADO' AS TipoPagoL,
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
  trim(tr.vendedor) AS CodigoVendedor,
  trim(tr.pedido) AS NumeroPedidoInterno,
  CAST('' AS CHAR(1)) AS ZonaVenta,
  CAST('' AS CHAR(1)) AS RutaVenta,
  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,
  tr.fecha AS FechaEmision,
  (
    CASE
      WHEN ISNULL (tr.CEDULA, '') = '' THEN REPLACE(TRIM(C.rnc),'-', '')
      ELSE REPLACE(tr.CEDULA, '-', '')
    END
  ) AS RNCComprador,  --El origen del rnc cambia en cada cliente y base de datos
  NULL AS IdentificadorExtranjero,
  --Razon Social del Comprador
  (
    CASE
      WHEN isnull (c.Nombre, '') = '' THEN tr.nombre
      WHEN isnull (c.Nombre, '') <> '' THEN c.Nombre
      ELSE 'CLIENTE'
    END
  ) AS RazonSocialComprador,
  '' AS ContactoComprador,
  '' AS CorreoComprador,
  c.Dire AS DireccionComprador,
  CAST('' AS CHAR(1)) AS MunicipioComprador, 
  CAST('' AS CHAR(1)) AS ProvinciaComprador,
  CAST('' AS CHAR(1)) AS PaisComprador,
  null AS FechaEntrega,
  CAST('' AS CHAR(1)) AS ContactoEntrega,
  CAST('' AS CHAR(1)) AS DireccionEntrega,
  c.Tele AS TelefonoAdicional,
  null AS FechaOrdenCompra,
  CAST('' AS CHAR(1)) AS NumeroOrdenCompra,
  tr.cliente AS CodigoInternoComprador,
  CAST('' AS CHAR(1)) AS ResponsablePago,
  CAST('' AS CHAR(1)) AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
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
  NULL AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  TRIM(tr.venname) AS NombreVendedor,			  
  
  --Seccion de Totales
  --Verficar si a estos montos le afecta el descuento
  Totales.MontoGravadoTotal as  MontoGravadoTotal,
  Totales.MontoGravadoI18 as MontoGravadoI1, --18
  Totales.MontoGravadoI16 as MontoGravadoI2, -- 16
  Totales.MontoGravadoIEX as MontoGravadoI3,  -- Exportacion
  Totales.MontoExento,
  Totales.ITBIS1,
  Totales.ITBIS2,
  Totales.ITBIS3,
  Totales.TotalITBIS,
  Totales.TotalITBIS1,
  Totales.TotalITBIS2,
  Totales.TotalITBIS3,
  Totales.IndicadorMontoGravadoI18,
  Totales.IndicadorMontoGravadoI16,
  Totales.IndicadorMontoGravadoINF,
  Totales.IndicadorMontoGravadoIEX,
  Totales.IndicadorMontoGravadoIE,

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
  
  tr.monto AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  NULL AS MontoPago,  
  NULL AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,

  -- Sesion de Nota de credito
  --NCF de la factura que se le esta aplicando la NC
  tr1.ncf AS NCFModificado,
  --RNC del NCF afectado
  /*REPLACE(tr.cedula, '-', '')*/ '' as RNCOtroContribuyente,
  --Fecha de la factura que se le esta aplicando la NC
  tr1.fecha AS FechaNCFModificado,
  --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
  --3: Corrige montos del NCF modificado
  3 AS CodigoModificacion,
  --Numero de de la factura que se le esta aplicando la NC
  tr.documento AS NumeroDocumentoNCFModificado,
  --Monto de la factura que se le esta aplicando la NC
  tr1.monto AS MontoNCFModificado,
  --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
  0 AS AbonoNCFModificado,
  --Monto de descuento a la factura que se le esta aplicando la NC
  0 AS DescuentoNCFModificado,
  --Monto Pendinete de la factura que se le esta aplicando la NC
  0 AS PendienteNCFModificado,
  --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
  --En caso de que sea una nota de credito, enviar la razon de la modificacion 
   tr.observa AS RazonModificacion,
  --Datos de Facturacion Electronica
  tr.fechacreacion,
  tr.Trackid,
  tr.FechaFirma,
  tr.CodigoSeguridad,
  tr.CodigoSeguridadCF,
  tr.Estadoimpresion AS EstadoImpresion,
  tr.ConteoImpresiones,
  tr.EstadoFiscal,
  tr.ResultadoEstadoFiscal,
  tr.MontoDGII,
  tr.MontoITBISDGII,		 

    CASE
        WHEN SUBSTRING(TR.ncf, 2, 2) = '32' AND TR.monto < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&MontoTotal=', round(TR.monto,2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
        WHEN SUBSTRING(TR.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TR.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
				CASE
					WHEN ISNULL (tr.CEDULA, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(tr.CEDULA), '-', ''))
					WHEN ISNULL (C.rnc, '') <> '' THEN CONCAT('&RncComprador=', REPLACE(TRIM(C.rnc), '-', ''))
					ELSE ''
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  tr.observa AS Observaciones,
  tr.creado AS Creadopor,
  tr.USUARIO AS Usuario,
  tr.USUARIO AS ModificadoPor,
  tr.cajero as Cajero,
  /*(
    CASE
      WHEN COALESCE(tr.observa1, '') <> '' THEN tr.observa1
      WHEN COALESCE(tr.observa3, '') <> '' THEN tr.observa3
      ELSE ''
    END
  )*/ '' AS NotaPermanente,
  /*tr.Descrip1*/ '' as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion
FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON c.cliente = tr.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 --LEFT OUTER JOIN dbo.ruta as r  WITH (NOLOCK) on r.ruta = tr.ruta
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = TR.RNCEmisor and Totales.eNCF = tr.NCF
 LEFT OUTER JOIN dbo.Transa01 AS tr1 WITH (nolock) ON tr1.numero = tr.documento and tr1.tipo = '03' -- Acceso a la factura a la que afecta
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('17'))
								 
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEEncabezadoCajachica]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     view [dbo].[vFEEncabezadoCajachica] as

--Caja Chica
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
    
    MAX(cc.documento) as NumeroFacturaInterna,
    MAX(cc.ncftipo) as TipoDocumento,
    MAX(SUBSTRING(cc.ncf, 1, 1)) as TipoECFL,
    MAX(SUBSTRING(cc.ncf, 2, 2)) as TipoECF,
    MAX(tn.Descripcion) as TipoECFL1,
    MAX(tn.Descripcion) as Descripcion,
    MAX(tn.Auxiliar) as Auxiliar,
    'CAJACHICA' as Tabla,
    'rncemisor' as campo1,
    'ncf' as campo2,
	cc.ncf AS eNCF,
    MAX(cc.FVencimientoNCF) as FechaVencimientoSecuencia,
    NULL as FechaLimitePago,
    0 as TerminoPagoN,
    CAST('' AS CHAR(100)) as TerminoPago,
    '0'as Almacen,
    0 as IndicadorNotaCredito,
    0 as IndicadorMontoGravado,
    '01' as TipoIngresos,
    1 as TipoPago,
    'CONTADO' as TipoPagoL,
    NULL as TipoCuentaPago,
    NULL as NumeroCuentaPago,
    NULL as BancoPago,
    NULL as FechaDesde,
    NULL as FechaHasta,
    NULL as TotalPaginas,
	REPLACE(cc.RNCEmisor, '-', '') AS RNCEmisor,
    MAX(e.TipodeIngresos) as TipodeIngresos,
	MAX(e.IndicadorEnvioDiferido) AS IndicadorEnvioDiferido,
	  --Emisor
	max(e.nombre) as RazonSocialEmisor,
	  CAST('' AS CHAR(1)) AS NombreComercial,
	  CAST('' AS CHAR(1)) AS Sucursal,
	  max(e.dire) as DireccionEmisor,
	  CAST('' AS CHAR(1)) AS Municipio,
	  CAST('' AS CHAR(1)) AS Provincia,
	  CAST('' AS CHAR(1)) as CorreoEmisor,
	  CAST('' AS CHAR(1)) as WebSite,
	  CAST('' AS CHAR(1)) as ActividadEconomica,
    MAX(e.Tele) as TelefonoEmisor1,
    CAST('' AS CHAR(100)) as TelefonoEmisor2,
    CAST('' AS CHAR(100)) as TelefonoEmisor3,
    CAST('' AS CHAR(100)) as CodigoVendedor,
    CAST('' AS CHAR(100)) as NumeroPedidoInterno,
    CAST('' AS CHAR(100)) as ZonaVenta,
    CAST('' AS CHAR(100)) as RutaVenta,
    CAST('' AS CHAR(100)) as InformacionAdicionalEmisor,
    MAX(cc.fecha) as FechaEmision,
    CAST('' AS CHAR(100)) as RNCComprador,
    null as IdentificadorExtranjero,
    CAST('' AS CHAR(100)) as RazonSocialComprador,
    CAST('' AS CHAR(100)) as ContactoComprador,
    CAST('' AS CHAR(100)) as CorreoComprador,
    CAST('' AS CHAR(100)) as DireccionComprador,
    CAST('' AS CHAR(100)) AS MunicipioComprador, 
    CAST('' AS CHAR(100)) as ProvinciaComprador,
    CAST('' AS CHAR(100)) as PaisComprador,
    null as FechaEntrega,
    CAST('' AS CHAR(100)) as ContactoEntrega,
    CAST('' AS CHAR(100)) as DireccionEntrega,
    CAST('' AS CHAR(100)) as TelefonoAdicional,
    null as FechaOrdenCompra,
    CAST('' AS CHAR(100)) as NumeroOrdenCompra,
    CAST('' AS CHAR(100)) as CodigoInternoComprador,
    CAST('' AS CHAR(100)) as ResponsablePago,
    CAST('' AS CHAR(100)) as Informacionadicionalcomprador,
    null as FechaEmbarque,
    CAST('' AS CHAR(100)) as NumeroEmbarque,
    CAST('' AS CHAR(100)) as NumeroContenedor,
    CAST('' AS CHAR(100)) as NumeroReferencia,
    CAST('' AS CHAR(100)) as NombrePuertoEmbarque,
    CAST('' AS CHAR(100)) as CondicionesEntrega,
    NULL as TotalFob,
    NULL as Seguro,
    NULL as Flete,
    NULL as OtrosGastos,
    NULL as TotalCif,
    NULL as RegimenAduanero,
    NULL as NombrePuertoSalida,
    NULL as NombrePuertoDesembarque,
    NULL as PesoBruto,
    NULL as PesoNeto,
    NULL as UnidadPesoBruto,
    NULL as UnidadPesoNeto,
    NULL as CantidadBulto,
    NULL as UnidadBulto,
    NULL as VolumenBulto,
    NULL as UnidadVolumen,
    NULL as ViaTransporte,
    NULL as PaisOrigen,
    NULL as DireccionDestino,
    NULL as PaisDestino,
    NULL as RNCIdentificacionCompaniaTransportista,
    NULL as NombreCompaniaTransportista,
    NULL as NumeroViaje,
    NULL as Conductor,
    NULL as DocumentoTransporte,
    NULL as Ficha,
    NULL as Placa,
    NULL as RutaTransporte,
    NULL as ZonaTransporte,
    NULL as NumeroAlbaran,
    NULL as MontoGravadoTotal,
    NULL as MontoGravadoI1,
    NULL as MontoGravadoI2,
    NULL as MontoGravadoI3,
    SUM(cc.debito - cc.credito) as MontoExento,
    NULL as ITBIS1,
    NULL as ITBIS2,
    0 as ITBIS3,
    NULL as TotalITBIS,
    NULL as TotalITBIS1,
    NULL as TotalITBIS2,
    0 as TotalITBIS3,
    0 as IndicadorMontoGravadoI18,
    0 as IndicadorMontoGravadoI16,
    1 as IndicadorMontoGravadoI0,
    NULL as MontoImpuestoAdicional,
    NULL as TipoImpuesto1,
    NULL as TasaImpuestoAdicional1,
    NULL as MontoImpuestoSelectivoConsumoEspecifico1,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem1,
    NULL as OtrosImpuestosAdicionales1,
    NULL as TipoImpuesto2,
    NULL as TasaImpuestoAdicional2,
    NULL as MontoImpuestoSelectivoConsumoEspecifico2,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem2,
    NULL as OtrosImpuestosAdicionales2,
    NULL as TipoImpuesto3,
    NULL as TasaImpuestoAdicional3,
    NULL as MontoImpuestoSelectivoConsumoEspecifico3,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem3,
    NULL as OtrosImpuestosAdicionales3,
    NULL as TipoImpuesto4,
    NULL as TasaImpuestoAdicional4,
    NULL as MontoImpuestoSelectivoConsumoEspecifico4,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem4,
    NULL as OtrosImpuestosAdicionales4,
    NULL as TipoImpuesto5,
    NULL as TasaImpuestoAdicional5,
    NULL as MontoImpuestoSelectivoConsumoEspecifico5,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem5,
    NULL as OtrosImpuestosAdicionales5,
    NULL as TipoImpuesto6,
    NULL as TasaImpuestoAdicional6,
    NULL as MontoImpuestoSelectivoConsumoEspecifico6,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem6,
    NULL as OtrosImpuestosAdicionales6,
    NULL as TipoImpuesto7,
    NULL as TasaImpuestoAdicional7,
    NULL as MontoImpuestoSelectivoConsumoEspecifico7,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem7,
    NULL as OtrosImpuestosAdicionales7,
    NULL as TipoImpuesto8,
    NULL as TasaImpuestoAdicional8,
    NULL as MontoImpuestoSelectivoConsumoEspecifico8,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem8,
    NULL as OtrosImpuestosAdicionales8,
    NULL as TipoImpuesto9,
    NULL as TasaImpuestoAdicional9,
    NULL as MontoImpuestoSelectivoConsumoEspecifico9,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem9,
    NULL as OtrosImpuestosAdicionales9,
    NULL as TipoImpuesto10,
    NULL as TasaImpuestoAdicional10,
    NULL as MontoImpuestoSelectivoConsumoEspecifico10,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem10,
    NULL as OtrosImpuestosAdicionales10,
    NULL as TipoImpuesto11,
    NULL as TasaImpuestoAdicional11,
    NULL as MontoImpuestoSelectivoConsumoEspecifico11,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem11,
    NULL as OtrosImpuestosAdicionales11,
    NULL as TipoImpuesto12,
    NULL as TasaImpuestoAdicional12,
    NULL as MontoImpuestoSelectivoConsumoEspecifico12,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem12,
    NULL as OtrosImpuestosAdicionales12,
    NULL as TipoImpuesto13,
    NULL as TasaImpuestoAdicional13,
    NULL as MontoImpuestoSelectivoConsumoEspecifico13,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem13,
    NULL as OtrosImpuestosAdicionales13,
    NULL as TipoImpuesto14,
    NULL as TasaImpuestoAdicional14,
    NULL as MontoImpuestoSelectivoConsumoEspecifico14,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem14,
    NULL as OtrosImpuestosAdicionales14,
    NULL as TipoImpuesto15,
    NULL as TasaImpuestoAdicional15,
    NULL as MontoImpuestoSelectivoConsumoEspecifico15,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem15,
    NULL as OtrosImpuestosAdicionales15,
    NULL as TipoImpuesto16,
    NULL as TasaImpuestoAdicional16,
    NULL as MontoImpuestoSelectivoConsumoEspecifico16,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem16,
    NULL as OtrosImpuestosAdicionales16,
    NULL as TipoImpuesto17,
    NULL as TasaImpuestoAdicional17,
    NULL as MontoImpuestoSelectivoConsumoEspecifico17,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem17,
    NULL as OtrosImpuestosAdicionales17,
    NULL as TipoImpuesto18,
    NULL as TasaImpuestoAdicional18,
    NULL as MontoImpuestoSelectivoConsumoEspecifico18,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem18,
    NULL as OtrosImpuestosAdicionales18,
    NULL as TipoImpuesto19,
    NULL as TasaImpuestoAdicional19,
    NULL as MontoImpuestoSelectivoConsumoEspecifico19,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem19,
    NULL as OtrosImpuestosAdicionales19,
    NULL as TipoImpuesto20,
    NULL as TasaImpuestoAdicional20,
    NULL as MontoImpuestoSelectivoConsumoEspecifico20,
    NULL as MontoImpuestoSelectivoConsumoAdvalorem20,
    NULL as OtrosImpuestosAdicionales20,
    NULL as NumeroLineaDoR1,
    NULL as TipoAjuste1,
    NULL as IndicadorNorma10071,
    NULL as DescripcionDescuentooRecargo1,
    NULL as TipoValor1,
    NULL as ValorDescuentooRecargo1,
    NULL as MontoDescuentooRecargo1,
    NULL as MontoDescuentooRecargoOtraMoneda1,
    NULL as IndicadorFacturacionDescuentooRecargo1,
    NULL as NumeroLineaDoR2,
    NULL as TipoAjuste2,
    NULL as IndicadorNorma10072,
    NULL as DescripcionDescuentooRecargo2,
    NULL as TipoValor2,
    NULL as ValorDescuentooRecargo2,
    NULL as MontoDescuentooRecargo2,
    NULL as MontoDescuentooRecargoOtraMoneda2,
    NULL as IndicadorFacturacionDescuentooRecargo2,
    NULL as NumeroLineaDoR3,
    NULL as TipoAjuste3,
    NULL as IndicadorNorma10073,
    NULL as DescripcionDescuentooRecargo3,
    NULL as TipoValor3,
    NULL as ValorDescuentooRecargo3,
    NULL as MontoDescuentooRecargo3,
    NULL as MontoDescuentooRecargoOtraMoneda3,
    NULL as IndicadorFacturacionDescuentooRecargo3,
    NULL as NumeroLineaDoR4,
    NULL as TipoAjuste4,
    NULL as IndicadorNorma10074,
    NULL as DescripcionDescuentooRecargo4,
    NULL as TipoValor4,
    NULL as ValorDescuentooRecargo4,
    NULL as MontoDescuentooRecargo4,
    NULL as MontoDescuentooRecargoOtraMoneda4,
    NULL as IndicadorFacturacionDescuentooRecargo4,
    NULL as NumeroLineaDoR5,
    NULL as TipoAjuste5,
    NULL as IndicadorNorma10075,
    NULL as DescripcionDescuentooRecargo5,
    NULL as TipoValor5,
    NULL as ValorDescuentooRecargo5,
    NULL as MontoDescuentooRecargo5,
    NULL as MontoDescuentooRecargoOtraMoneda5,
    NULL as IndicadorFacturacionDescuentooRecargo5,
    NULL as NumeroLineaDoR6,
    NULL as TipoAjuste6,
    NULL as IndicadorNorma10076,
    NULL as DescripcionDescuentooRecargo6,
    NULL as TipoValor6,
    NULL as ValorDescuentooRecargo6,
    NULL as MontoDescuentooRecargo6,
    NULL as MontoDescuentooRecargoOtraMoneda6,
    NULL as IndicadorFacturacionDescuentooRecargo6,
    NULL as NumeroLineaDoR7,
    NULL as TipoAjuste7,
    NULL as IndicadorNorma10077,
    NULL as DescripcionDescuentooRecargo7,
    NULL as TipoValor7,
    NULL as ValorDescuentooRecargo7,
    NULL as MontoDescuentooRecargo7,
    NULL as MontoDescuentooRecargoOtraMoneda7,
    NULL as IndicadorFacturacionDescuentooRecargo7,
    NULL as NumeroLineaDoR8,
    NULL as TipoAjuste8,
    NULL as IndicadorNorma10078,
    NULL as DescripcionDescuentooRecargo8,
    NULL as TipoValor8,
    NULL as ValorDescuentooRecargo8,
    NULL as MontoDescuentooRecargo8,
    NULL as MontoDescuentooRecargoOtraMoneda8,
    NULL as IndicadorFacturacionDescuentooRecargo8,
    NULL as NumeroLineaDoR9,
    NULL as TipoAjuste9,
    NULL as IndicadorNorma10079,
    NULL as DescripcionDescuentooRecargo9,
    NULL as TipoValor9,
    NULL as ValorDescuentooRecargo9,
    NULL as MontoDescuentooRecargo9,
    NULL as MontoDescuentooRecargoOtraMoneda9,
    NULL as IndicadorFacturacionDescuentooRecargo9,
    NULL as NumeroLineaDoR10,
    NULL as TipoAjuste10,
    NULL as IndicadorNorma100710,
    NULL as DescripcionDescuentooRecargo10,
    NULL as TipoValor10,
    NULL as ValorDescuentooRecargo10,
    NULL as MontoDescuentooRecargo10,
    NULL as MontoDescuentooRecargoOtraMoneda10,
    NULL as IndicadorFacturacionDescuentooRecargo10,
    NULL as NumeroLineaDoR11,
    NULL as TipoAjuste11,
    NULL as IndicadorNorma100711,
    NULL as DescripcionDescuentooRecargo11,
    NULL as TipoValor11,
    NULL as ValorDescuentooRecargo11,
    NULL as MontoDescuentooRecargo11,
    NULL as MontoDescuentooRecargoOtraMoneda11,
    NULL as IndicadorFacturacionDescuentooRecargo11,
    NULL as NumeroLineaDoR12,
    NULL as TipoAjuste12,
    NULL as IndicadorNorma100712,
    NULL as DescripcionDescuentooRecargo12,
    NULL as TipoValor12,
    NULL as ValorDescuentooRecargo12,
    NULL as MontoDescuentooRecargo12,
    NULL as MontoDescuentooRecargoOtraMoneda12,
    NULL as IndicadorFacturacionDescuentooRecargo12,
    NULL as NumeroLineaDoR13,
    NULL as TipoAjuste13,
    NULL as IndicadorNorma100713,
    NULL as DescripcionDescuentooRecargo13,
    NULL as TipoValor13,
    NULL as ValorDescuentooRecargo13,
    NULL as MontoDescuentooRecargo13,
    NULL as MontoDescuentooRecargoOtraMoneda13,
    NULL as IndicadorFacturacionDescuentooRecargo13,
    NULL as NumeroLineaDoR14,
    NULL as TipoAjuste14,
    NULL as IndicadorNorma100714,
    NULL as DescripcionDescuentooRecargo14,
    NULL as TipoValor14,
    NULL as ValorDescuentooRecargo14,
    NULL as MontoDescuentooRecargo14,
    NULL as MontoDescuentooRecargoOtraMoneda14,
    NULL as IndicadorFacturacionDescuentooRecargo14,
    NULL as NumeroLineaDoR15,
    NULL as TipoAjuste15,
    NULL as IndicadorNorma100715,
    NULL as DescripcionDescuentooRecargo15,
    NULL as TipoValor15,
    NULL as ValorDescuentooRecargo15,
    NULL as MontoDescuentooRecargo15,
    NULL as MontoDescuentooRecargoOtraMoneda15,
    NULL as IndicadorFacturacionDescuentooRecargo15,
    NULL as NumeroLineaDoR16,
    NULL as TipoAjuste16,
    NULL as IndicadorNorma100716,
    NULL as DescripcionDescuentooRecargo16,
    NULL as TipoValor16,
    NULL as ValorDescuentooRecargo16,
    NULL as MontoDescuentooRecargo16,
    NULL as MontoDescuentooRecargoOtraMoneda16,
    NULL as IndicadorFacturacionDescuentooRecargo16,
    NULL as NumeroLineaDoR17,
    NULL as TipoAjuste17,
    NULL as IndicadorNorma100717,
    NULL as DescripcionDescuentooRecargo17,
    NULL as TipoValor17,
    NULL as ValorDescuentooRecargo17,
    NULL as MontoDescuentooRecargo17,
    NULL as MontoDescuentooRecargoOtraMoneda17,
    NULL as IndicadorFacturacionDescuentooRecargo17,
    NULL as NumeroLineaDoR18,
    NULL as TipoAjuste18,
    NULL as IndicadorNorma100718,
    NULL as DescripcionDescuentooRecargo18,
    NULL as TipoValor18,
    NULL as ValorDescuentooRecargo18,
    NULL as MontoDescuentooRecargo18,
    NULL as MontoDescuentooRecargoOtraMoneda18,
    NULL as IndicadorFacturacionDescuentooRecargo18,
    NULL as NumeroLineaDoR19,
    NULL as TipoAjuste19,
    NULL as IndicadorNorma100719,
    NULL as DescripcionDescuentooRecargo19,
    NULL as TipoValor19,
    NULL as ValorDescuentooRecargo19,
    NULL as MontoDescuentooRecargo19,
    NULL as MontoDescuentooRecargoOtraMoneda19,
    NULL as IndicadorFacturacionDescuentooRecargo19,
    NULL as NumeroLineaDoR20,
    NULL as TipoAjuste20,
    NULL as IndicadorNorma100720,
    NULL as DescripcionDescuentooRecargo20,
    NULL as TipoValor20,
    NULL as ValorDescuentooRecargo20,
    NULL as MontoDescuentooRecargo20,
    NULL as MontoDescuentooRecargoOtraMoneda20,
    NULL as IndicadorFacturacionDescuentooRecargo20,
    '' as NombreVendedor,
    SUM(cc.debito - cc.credito) as MontoTotal,
    NULL as MontoNoFacturable,
    NULL as MontoPeriodo,
    NULL as SaldoAnterior,
    NULL as MontoAvancePago,
    SUM(cc.debito - cc.credito) as MontoPago,
    NULL as ValorPagar,
    sum(cc.itbisret) as TotalITBISRetenido,
    NULL as TotalISRRetencion,
    NULL as TotalITBISPercepcion,
	NULL as TotalISRPercepcion,
    'DOP' as TipoMoneda,
    'PESO DOMINICANO' as TipoMonedaL,
    1 as TipoCambio,
    NULL as MontoGravadoTotalOtraMoneda,
    NULL as MontoGravado1OtraMoneda,
    NULL as MontoGravado2OtraMoneda,
    NULL as MontoGravado3OtraMoneda,
    NULL as MontoExentoOtraMoneda,
    NULL as TotalITBISOtraMoneda,
    NULL as TotalITBIS1OtraMoneda,
    NULL as TotalITBIS2OtraMoneda,
    NULL as TotalITBIS3OtraMoneda,
    NULL as MontoImpuestoAdicionalOtraMoneda,
    NULL as MontoTotalOtraMoneda,

    

	
				 --NCF de la factura que se le esta aplicando la NC
			 CAST('' AS CHAR(100)) AS NCFModificado,

			     CAST('' AS CHAR(100)) as RNCOtroContribuyente,
			 
			 --Fecha de la factura que se le esta aplicando la NC
			 null AS FechaNCFModificado, 
			 
			 --Razon de modificacion de la factura que se le esta aplicando la NC (Segun tabla DGII)
			 --3: Corrige montos del NCF modificado
			 0 AS CodigoModificacion, 
			 
			 --Numero de de la factura que se le esta aplicando la NC
			 CAST('' AS CHAR(100)) AS NumeroDocumentoNCFModificado, 
			 
			 --Monto de la factura que se le esta aplicando la NC
			 0 as MontoNCFModificado,

			 --Abono a la factura que se le esta aplicando la NC (valor de la nota de credito)
			 0 as AbonoNCFModificado,
			 
			 --Monto de descuento a la factura que se le esta aplicando la NC
			 0 as DescuentoNCFModificado,

			 --Monto Pendinete de la factura que se le esta aplicando la NC
			 0 as PendienteNCFModificado,

			 --Razon de Modficiacion especificada por el usurio de la factura que se le esta aplicando la NC en el sistema
			CAST('' AS CHAR(100)) AS RazonModificacion, 
			 
	


    MAX(cc.fechacreacion) as fechacreacion,
    MAX(cc.Trackid) as Trackid,
    MAX(cc.FechaFirma) as FechaFirma,
    MAX(cc.CodigoSeguridad) as CodigoSeguridad,
    '' as CodigoSeguridadCF,
    MAX(cc.Estadoimpresion) as EstadoImpresion,
    NULL as ConteoImpresiones,
    MAX(cc.EstadoFiscal) as EstadoFiscal,
    MAX(CONCAT(
        'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?',
        'RncEmisor=', TRIM(cc.rncemisor),
        '&ENCF=', TRIM(cc.ncf),
        '&FechaEmision=', dbo.FNFechaDMY(cc.fecha),
        '&MontoTotal=', (cc.debito - cc.credito),
        '&FechaFirma=', REPLACE(TRIM(cc.FechaFirma), ' ', '%20'),
        '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](trim(cc.CodigoSeguridad))
    )) as URLQR,
    max(cc.recibido) as Observaciones,
    '' as Creadopor,
    '' as ModificadoPor,
    max(cc.BENeFICIARIO) as NotaPermanente,
  '' as NotaPago
FROM dbo.cajachica AS cc  WITH (NOLOCK)
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn ON tn.Codigo = SUBSTRING(cc.ncf, 2, 2) 
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cc.RNCEmisor  = e.rnc 
 CROSS JOIN AmbienteInfo AI 
WHERE cc.ncftipo IN ('GM') 
AND (cc.ncf IS NOT NULL) 
AND (cc.ncf <> '') 
AND (cc.EstadoFiscal IS NOT NULL)
AND SUBSTRING(cc.ncf, 1, 1) = 'E'
GROUP BY cc.ncf, cc.RNCEmisor
GO
/****** Object:  View [dbo].[vFETablaDescuentosyRecargos]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     view [dbo].[vFETablaDescuentosyRecargos] AS
 SELECT 
        td.numero as NumeroFacturaInterna,
		td.tipo as TipoDocumento,
		SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
		SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
		tr.ncf AS eNCF,
		tr.RNCEmisor,
        1 as NumeroLineaDoR,
        'D' as TipoAjuste,
        null as IndicadorNorma1007,
        'DESCUENTO A PRODUCTO'  as DescripcionDescuentooRecargo,
        '$' as TipoValor,
        null as ValorDescuentooRecargo,
		FORMAT(td.montodesc, '0.00') as MontoDescuentooRecargo,
        null as MontoDescuentooRecargoOtraMoneda,
        i.codigodgii as IndicadorFacturacionDescuentooRecargo

 from tradetalle td WITH (NOLOCK)

 LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
 LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
 LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo

 where  COALESCE(td.montodesc,0) > 0 and 0>0


GO
/****** Object:  View [dbo].[vFETablaImpuestosAdicionales]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     view [dbo].[vFETablaImpuestosAdicionales]  as 
 SELECT 
        td.numero as NumeroFacturaInterna,
		td.tipo as TipoDocumento,
		SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
		SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
		tr.ncf AS eNCF,
		tr.RNCEmisor,
        null TipoImpuesto,
        null TasaImpuestoAdicional,
        null MontoImpuestoSelectivoConsumoEspecifico,
        null MontoImpuestoSelectivoConsumoAdvalorem,
        null OtrosImpuestosAdicionales
 
 from tradetalle td WITH (NOLOCK)

 LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
 LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
 LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo

 Where 0>1 and 0>0
GO
/****** Object:  View [dbo].[vFETablaPago]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE     VIEW   [dbo].[vFETablaPago] AS
WITH Pagos AS (
    SELECT 
        tr.numero AS NumeroFacturaInterna, 
        tr.tipo AS TipoDocumento, 
        tr.RNCEmisor, 
        tr.ncf AS eNCF, 
        tr.EstadoFiscal, 
        tr.trackid, 
        tr.FechaFirma, 
        tr.CodigoSeguridad, 
        tr.EstadoImpresion, 
        fp.FormaPago, 
        fp.Descrip, 
        COALESCE(tr.tasa, 1) AS TipoCambio, 
        CASE 
            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN fp.MontoPago 
            ELSE fp.MontoPago * tr.tasa 
        END AS MontoPago
    FROM transa01 tr
    CROSS APPLY (
        VALUES
            (0, 'Devuelta', tr.devuelta),
            (1, 'Efectivo', tr.efectivo),
            (2, 'Cheque/Transferencia/Deposito', tr.transferencia + tr.cheque),
            (3, 'Tarjeta', tr.tarjeta),
            (CASE WHEN tr.tipo IN ('04', '34') THEN 4 END, 
             CASE WHEN tr.tipo IN ('04', '34') THEN 'Venta a Credito' END, 
             CASE WHEN tr.tipo IN ('04', '34') THEN tr.monto END)
    ) AS fp(FormaPago, Descrip, MontoPago)
    WHERE fp.MontoPago IS NOT NULL AND fp.MontoPago <> 0 AND SUBSTRING(tr.ncf, 1, 1) = 'E'

   )


SELECT * FROM Pagos





GO
/****** Object:  View [dbo].[vFETotales]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

create       VIEW   [dbo].[vFETotales] AS 	
	
	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		--Facturas


		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		AND SUBSTRING(tr.ncf, 1, 1) = 'E'
		AND tr.tipo in ('03','04', '34','33') -- Todas las ventas a contado y a credito en pesos y dolares
		AND tr.RNCEmisor IS NOT NULL
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))

		-- Devoluciones Contado
		Union All
		SELECT
			tr.rncemisor,
			tr.ncf AS eNCF,
			td.numero AS NumeroFacturaInterna,
			td.tipo AS TipoDocumento,

			-- Usa MAX para determinar el indicador según la fecha más reciente
			CASE 
				WHEN DATEDIFF(DAY, MAX(tr1.fecha), MAX(tr.fecha)) > 30 THEN 4
				ELSE MAX(i.codigodgii)
			END AS IndicadorFacturacion,

			CASE 
				WHEN DATEDIFF(DAY, MAX(tr1.fecha), MAX(tr.fecha)) > 30 THEN 'E'
				ELSE MAX(i.Siglas)
			END AS Siglas,

			COALESCE(MAX(tr.tasa), 1) AS TipoCambio,
			SUM(td.descuen) AS MontoDescuento,
			SUM(COALESCE(td.montoitbis, 0)) AS MontoImpuesto,
			SUM(COALESCE(td.Monto1, 0)) AS MontoTotal
		FROM tradetalle AS td WITH (NOLOCK)
		LEFT JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo
		LEFT JOIN dbo.Transa01 AS tr1 WITH (NOLOCK) ON tr1.numero = td.documento AND tr1.tipo IN ('03')
		WHERE tr.estadofiscal IS NOT NULL
        AND SUBSTRING(tr.ncf, 1, 1) = 'E'
		AND td.tipo = '17'
		AND tr.RNCEmisor IS NOT NULL	
		GROUP BY 
		tr.rncemisor,
		tr.ncf,
		td.numero,
		td.tipo
  
  -- Devoluciones Crédito
		Union All
		SELECT
			cxc.rncemisor,
			cxc.ncf AS eNCF,
			td.numero AS NumeroFacturaInterna,
			td.tipo AS TipoDocumento,

			-- Usa MAX para determinar el indicador según la fecha más reciente
			CASE 
				WHEN DATEDIFF(DAY, MAX(tr1.fecha), MAX(cxc.fecha)) > 30 THEN 4
				ELSE MAX(i.codigodgii)
			END AS IndicadorFacturacion,

			CASE 
				WHEN DATEDIFF(DAY, MAX(tr1.fecha), MAX(cxc.fecha)) > 30 THEN 'E'
				ELSE MAX(i.Siglas)
			END AS Siglas,

			COALESCE(MAX(cxc.tasa), 1) AS TipoCambio,
			SUM(td.descuen) AS MontoDescuento,
			SUM(COALESCE(td.montoitbis, 0)) AS MontoImpuesto,
			SUM(COALESCE(td.Monto1, 0)) AS MontoTotal
		FROM tradetalle AS td WITH (NOLOCK)
		LEFT JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT JOIN dbo.cxcmovi1 AS cxc WITH (NOLOCK) ON cxc.documento = td.numero AND cxc.tipomovi = '03'  and td.tipo = '05'
		LEFT JOIN dbo.Transa01 AS tr1 WITH (NOLOCK) ON tr1.numero = td.documento AND tr1.tipo IN ('03')
		WHERE cxc.estadofiscal IS NOT NULL
        AND SUBSTRING(cxc.ncf, 1, 1) = 'E'
		AND cxc.tipomovi = '03'
		AND cxc.RNCEmisor IS NOT NULL	
		GROUP BY 
		cxc.rncemisor,
		cxc.ncf,
		td.numero,
		td.tipo
		-- Notas de creditos Directas
		union all
		Select   
			cxc.rncemisor,cxc.ncf as eNCF,cxc.documento as NumeroFacturaInterna,cxc.tipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			sum(cxc.descuen) as MontoDescuento,
			sum(COALESCE(cxc.impuesto, 0 )) as MontoImpuesto,
			sum(COALESCE(cxc.Monto, 0 )) AS MontoTotal
		from  cxcmovi1 cxc WITH (NOLOCK)
		where cxc.estadofiscal is not null
		AND SUBSTRING(cxc.ncf, 1, 1) = 'E'
		AND cxc.RNCEmisor IS NOT NULL
		group by cxc.rncemisor,cxc.ncf,cxc.documento,cxc.tipo


		-- gastos Menores en Tabla de Caja Chica
		Union All
		Select  
			cc.rncemisor,cc.ncf as eNCF,cc.documento as NumeroFacturaInterna,cc.ncftipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			SUM(cc.debito - cc.credito) AS MontoTotal
		from  cajachica  AS cc WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cc.ncf, 1, 1) = 'E'
		AND cc.RNCEmisor IS NOT NULL
		group by cc.rncemisor,cc.ncf,cc.documento,cc.ncftipo


		--gastos Menores en Tabla cxpMovi1
		union all
		Select  
			cxp.rncemisor,cxp.ncf as eNCF,cxp.documento as NumeroFacturaInterna,cxp.ncf as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			cxp.monto AS MontoTotal
		from  cxpmovi1  AS cxp WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
		AND cxp.RNCEmisor IS NOT NULL
		and cxp.tipoMOVI IN ('07')
		AND cxp.gmenor = 1


		union all
		-- Proveedor Informal
		Select  
			cxp.rncemisor,cxp.ncf as eNCF,cxp.documento as NumeroFacturaInterna,cxp.tipomovi as TipoDocumento,
			(case
			 when cxp.impuesto >0 then 1
			 else 4
			end
			) AS IndicadorFacturacion,
			(case
			 when cxp.impuesto >0 then ''
			 else 'E'
			end
			)  AS SiglasImpuesto, 
			1 as TipoCambio,
			0 as MontoDescuento,
			cxp.impuesto as MontoImpuesto,
			cxp.monto AS MontoTotal
		from  cxpmovi1  AS cxp WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
		AND cxp.RNCEmisor IS NOT NULL
		and cxp.tipoMOVI IN ('07')
		AND cxp.informal = 1
		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
GO
/****** Object:  View [dbo].[vFETotalesold]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     VIEW   [dbo].[vFETotalesold] AS 	
	
	SELECT 
		RNCEmisor,
		eNCF,
		NumeroFacturaInterna,
		TipoDocumento,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
		Select   
			tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
			CASE
				WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
				WHEN SUBSTRING(tr.ncf, 2, 2)=44 THEN 4
				ELSE i.codigodgii 
			END AS IndicadorFacturacion,
			i.Siglas AS SiglasImpuesto, (COALESCE(tr.tasa, 1 )) as TipoCambio,
			sum(td.descuen) as MontoDescuento,
			sum(COALESCE(td.montoitbis, 0 )) as MontoImpuesto,
			sum(COALESCE(td.Monto1, 0 )) AS MontoTotal
		from  tradetalle AS td WITH (NOLOCK)
		LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
		LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
		LEFT OUTER JOIN dbo.Transa01 as tr WITH (NOLOCK) ON tr.numero = td.numero and tr.tipo = td.tipo
		where estadofiscal is not null
		AND SUBSTRING(tr.ncf, 1, 1) = 'E'
		AND tr.RNCEmisor IS NOT NULL
		group by tr.rncemisor,tr.ncf,td.numero,td.tipo, i.codigodgii ,  i.Siglas, (COALESCE(tr.tasa, 1 ))

		Union All
		-- gastos Menores en Tabla de Caja Chica
		Select  
			cc.rncemisor,cc.ncf as eNCF,cc.documento as NumeroFacturaInterna,cc.ncftipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			SUM(cc.debito - cc.credito) AS MontoTotal
		from  cajachica  AS cc WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cc.ncf, 1, 1) = 'E'
		AND cc.RNCEmisor IS NOT NULL
		group by cc.rncemisor,cc.ncf,cc.documento,cc.ncftipo

		union all
		--gastos Menores en Tabla cxpMovi1
		Select  
			cxp.rncemisor,cxp.ncf as eNCF,cxp.documento as NumeroFacturaInterna,cxp.ncf as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			0 as MontoDescuento,
			0 as MontoImpuesto,
			cxp.monto AS MontoTotal
		from  cxpmovi1  AS cxp WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
		AND cxp.RNCEmisor IS NOT NULL
		and cxp.tipoMOVI IN ('07')
		AND cxp.gmenor = 1

		union all
		-- Notas de reditos Directas
		Select   
			cxc.rncemisor,cxc.ncf as eNCF,cxc.documento as NumeroFacturaInterna,cxc.tipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			sum(cxc.descuen) as MontoDescuento,
			sum(COALESCE(cxc.impuesto, 0 )) as MontoImpuesto,
			sum(COALESCE(cxc.Monto, 0 )) AS MontoTotal
		from  cxcmovi1 cxc WITH (NOLOCK)
		where cxc.estadofiscal is not null
		AND SUBSTRING(cxc.ncf, 1, 1) = 'E'
		AND cxc.RNCEmisor IS NOT NULL
		group by cxc.rncemisor,cxc.ncf,cxc.documento,cxc.tipo

		union all
		-- Proveedor Informal
		Select  
			cxp.rncemisor,cxp.ncf as eNCF,cxp.documento as NumeroFacturaInterna,cxp.tipomovi as TipoDocumento,
			(case
			 when cxp.impuesto >0 then 1
			 else 4
			end
			) AS IndicadorFacturacion,
			(case
			 when cxp.impuesto >0 then ''
			 else 'E'
			end
			)  AS SiglasImpuesto, 
			1 as TipoCambio,
			0 as MontoDescuento,
			cxp.impuesto as MontoImpuesto,
			cxp.monto AS MontoTotal
		from  cxpmovi1  AS cxp WITH (NOLOCK)
		where estadofiscal is not null
		AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
		AND cxp.RNCEmisor IS NOT NULL
		and cxp.tipoMOVI IN ('07')
		AND cxp.informal = 1
		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
GO
/****** Object:  View [dbo].[vInformacionAdicional]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[vInformacionAdicional]
AS
SELECT        FechaEmbarque, NumeroEmbarque, NumeroContenedor, NumeroReferencia, NombrePuertoEmbarque, CondicionesEntrega, TotalFob, Seguro, Flete, TotalCif, RegimenAduanero, NombrePuertaSalida, 
                         NombrePuertoDesembarque, PesoBruto, PesoNeto, UnidadPesoBruto, UnidadPesoNeto, CantidadBulto, UnidadBulto, VolumenBulto, UnidadVolumen, ViaTransporte, PaisOrigen, DireccionDestino, PaisDestino, NumeroAlbaran, 
                         documento, ContactoEntrega, FechaEntrega, DireccionEntrega, TelefonoAdicional
FROM            dbo.InformacionAdicional
GO
/****** Object:  View [dbo].[vproducto]    Script Date: 24-10-2025 5:55:23 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE     view [dbo].[vproducto] as
SELECT 
p.producto, p.descrip, u.descrip unidad, n.referencia, p.poferta,p.descuen,
n.precio1, n.precio2, n.precio3, n.precio4, p.costo1,p.costo2, p.Comision,
p.CambiarPrecio, p.garantia, p.impuesto, p.costo3, p.noExistencia, p.activo, 
p.serializado,p.tiposerializado, p.servicio 
FROM unidadProducto n
inner join unidad u on u.unidad=n.unidad
inner join producto p on p.producto=n.producto
WHERE n.pdefault='1';
GO
