
/****** Object:  View [dbo].[vFEDevCRRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW   [dbo].[vFEDevCRRD] AS 
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
  (
    CASE
      WHEN tr.tipo = '17' THEN 1
      WHEN tr.tipo = '05' THEN 2
    END
  ) AS TipoPago,
  (
    CASE
      WHEN tr.tipo = '17' THEN 'CONTADO'
      WHEN tr.tipo = '05' THEN 'CREDITO'
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
  Totales.MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda,

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
					WHEN LEN(TRIM(REPLACE(c.rnc1, '-', ''))) > 0 
					THEN CONCAT('&RncComprador=', REPLACE(TRIM(c.rnc1), '-', ''))
                ELSE '' 
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  '' AS Observaciones,
  tr.creado AS Creadopor,
  tr.USUARIO AS Usuario,
  tr.USUARIO AS ModificadoPor,
  tr.cajero as Cajero,
   COALESCE(tr.observa, '')+'|' + COALESCE(tr.observa1, '')+'|'+ COALESCE(tr.observa3, '') 
   AS NotaPermanente,  
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
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = TR.RNCEmisor and Totales.eNCF = tr.ncf
 LEFT OUTER JOIN dbo.Transa01 AS tr1 WITH (nolock) ON tr1.numero = tr.documento and tr1.tipo = '04' -- Acceso a la factura a la que afecta
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('05'))
								 
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEDevCORD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW   [dbo].[vFEDevCORD] AS 
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
  (
    CASE
      WHEN tr.tipo = '17' THEN 1
      WHEN tr.tipo = '05' THEN 2
    END
  ) AS TipoPago,
  (
    CASE
      WHEN tr.tipo = '17' THEN 'CONTADO'
      WHEN tr.tipo = '05' THEN 'CREDITO'
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
  Totales.MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda,
  
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
  left(tr.observa,90) AS RazonModificacion,
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
					WHEN LEN(TRIM(REPLACE(c.rnc1, '-', ''))) > 0 
					THEN CONCAT('&RncComprador=', REPLACE(TRIM(c.rnc1), '-', ''))
                ELSE '' 
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  '' AS Observaciones,
  tr.creado AS Creadopor,
  tr.USUARIO AS Usuario,
  tr.USUARIO AS ModificadoPor,
  tr.cajero as Cajero,
   COALESCE(tr.observa, '')+'|' + COALESCE(tr.observa1, '')+'|'+ COALESCE(tr.observa3, '') 
   AS NotaPermanente,
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
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = TR.RNCEmisor and Totales.eNCF = tr.ncf
 LEFT OUTER JOIN dbo.Transa01 AS tr1 WITH (nolock) ON tr1.numero = tr.documento and tr1.tipo = '03' -- Acceso a la factura a la que afecta
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('17'))
								 
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEVentaRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW   [dbo].[vFEVentaRD] AS 
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
 --Datos de Tradetalle
 --Datos de las tablas para construir las Facturas 
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
  try_CAST(try_CAST(tr.pedido AS INT) as nvarchar(20)) AS NumeroPedidoInterno,
  --LEFT(trim(tr.zona)+' '+trim(z.descrip), 20) AS ZonaVenta,
  CAST('' AS CHAR(1)) AS ZonaVenta,
  --Esta Linea se utliza en Lucas
  --LEFT(trim(tr.ruta)+' '+trim(r.descrip),20) AS RutaVenta,
  '' AS RutaVenta,

  CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,

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
  '' AS ContactoComprador,
  '' AS CorreoComprador,
  (
    CASE
      WHEN ISNULL (tr.dire, '') = '' THEN REPLACE(c.dire, '-', '')
      ELSE REPLACE(tr.dire, '-', '')
    END
  ) AS DireccionComprador,
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
  Totales.MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda,

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
					WHEN LEN(TRIM(REPLACE(c.rnc1, '-', ''))) > 0 
					THEN CONCAT('&RncComprador=', REPLACE(TRIM(c.rnc1), '-', ''))
                ELSE '' 
				END,  --El origen del rnc cambia en cada cliente y base de datos
				'&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round(TR.monto,2),
                '&FechaFirma=', REPLACE(TRIM(TR.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
    END  AS URLQR ,

  '' AS Observaciones,
  tr.creado AS Creadopor,
  tr.usuario AS Usuario,
  --tr.modificado AS ModificadoPor,
  '' AS ModificadoPor,
  tr.cajero as Cajero,
   COALESCE(tr.observa, '')+'|' + COALESCE(tr.observa1, '')+'|'+ COALESCE(tr.observa3, '') 
   AS NotaPermanente,  
  --tr.Descrip1 as NotaPago,
  '' as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion
FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON c.cliente = tr.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = TR.RNCEmisor and Totales.eNCF = tr.ncf and Totales.NumeroFacturaInterna = tr.numero and Totales.TipoDocumento = tr.tipo
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('03', '04'))
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)


GO
/****** Object:  View [dbo].[vFENCDIRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFENCDIRD] AS 
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
      WHEN DATEDIFF(DAY, cxcd.fecha1, cxc.fecha) >30 THEN 1
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
  REPLACE(TRIM(c.rnc1), '-', '') AS RNCComprador,
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
  Totales.MontoGravadoTotalOtraMoneda,
  Totales.MontoGravado1OtraMoneda,
  Totales.MontoGravado2OtraMoneda,
  Totales.MontoGravado3OtraMoneda,
  Totales.MontoExentoOtraMoneda,
  Totales.TotalITBISOtraMoneda,
  Totales.TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3OtraMoneda,
  Totales.MontoImpuestoAdicionalOtraMoneda,
  Totales.MontoTotalOtraMoneda,

  cxc.monto  AS MontoTotal,
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
  '' as CodigoSeguridadCF,
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
					WHEN LEN(TRIM(REPLACE(c.rnc1, '-', ''))) > 0 
					THEN CONCAT('&RncComprador=', REPLACE(TRIM(c.rnc1), '-', ''))
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
  ''  AS NotaPermanente,
  '' as NotaPago,
  '' as NotaAntesDeProductos,
  '' as EquipoImpresion



FROM
  dbo.cxcmovi1 AS cxc WITH (NOLOCK) 
  LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(cxc.ncf, 2, 2) 
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON cxc.RNCEmisor = e.rnc 
  LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON trim(c.cliente) = trim(cxc.cliente)
  LEFT OUTER JOIN cxcdetalle1 AS cxcd ON trim(cxc.documento) = trim(cxcd.documento) AND trim(cxc.tipomovi) = trim(cxcd.tipomovi)
  LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = cxc.RNCEmisor and Totales.eNCF = cxc.ncf
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxc.tipomovi IN ( '02'))
  --and (COALESCE(cxc.tasa, 1.00) =1 OR COALESCE(cxc.tasa, 1.00) = 0)
  AND (cxc.ncf IS NOT NULL)
  AND (cxc.ncf <> '')
  AND (cxc.EstadoFiscal IS NOT NULL)

GO
/****** Object:  View [dbo].[vFEEncabezado]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW   [dbo].[vFEEncabezado] AS 


Select * from vFEVentaRD

union all

Select * from vFEDevCORD

union all

Select * from vFEDevCRRD

union all

Select * from vFENCDIRD 






GO
/****** Object:  View [dbo].[vFENCDIDEtRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFENCDIDEtRD] as

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
/****** Object:  View [dbo].[vFEDevCRDetRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFEDevCRDetRD] as
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
  p.unidad as UnidadMedidaL,
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
  td.tipo IN ('05')
  AND (tr.EstadoFiscal IS NOT NULL) 
  AND COALESCE(tr.tasa, 1)= 1


GO
/****** Object:  View [dbo].[vFEDevCODetRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFEDevCODetRD] as
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
  p.unidad as UnidadMedidaL,
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
  td.tipo IN ('17')
  AND (tr.EstadoFiscal IS NOT NULL) 
  AND COALESCE(tr.tasa, 1)= 1


GO
/****** Object:  View [dbo].[vFEVentaDetRD]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFEVentaDetRD] as
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
  trim(td.producto)  AS CodigoItem1,
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
    WHEN td.cantidad < 0 THEN td.cantidad * - 1
    ELSE td.cantidad
  END AS CantidadItem,
  '' AS UnidadMedida,
  p.unidad as UnidadMedidaL,
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
  td.monto1 AS MontoItem,
  p.NotaImpresion
FROM
  dbo.tradetalle AS td WITH (NOLOCK)
  LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
  LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor = e.rnc
  
WHERE
  (td.tipo IN ('03', '04'))
  AND (tr.EstadoFiscal IS NOT NULL) 
  AND td.precio >=0
GO
/****** Object:  View [dbo].[vFEDetalle]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFEDetalle] as

Select * from vFEVentaDetRD

union all

Select * from vFEDevCODetRD

union all

Select * from vFEDevCRDetRD

union all

Select * from vFENCDIDEtRD

GO
/****** Object:  View [dbo].[vMonitorSentences]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[vMonitorSentences]
AS
SELECT        CAST(f.FechaEmision AS DATE) AS FechaEmision, f.NumeroFacturaInterna AS Factura, f.TipoPagoL AS TipoVenta, f.TipoECF, f.eNCF, f.EstadoFiscal, ef.Descrip AS DescripcionEstadoFiscal, f.EstadoImpresion, 
                         LEFT(f.NumeroFacturaInterna, 1) AS Caja, f.URLQR AS URLC, f.ResultadoEstadoFiscal, f.MontoTotal AS MontoFacturado, f.TotalITBIS AS ITBISFacturado, f.MontoDGII, f.MontoITBISDGII, f.RNCEmisor
FROM            dbo.vFEEncabezado AS f LEFT OUTER JOIN
                         dbo.EstadoFiscal AS ef ON f.EstadoFiscal = ef.estado
GO
/****** Object:  View [dbo].[secuenciasGlobales]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
--VISTA SECUENCIAS GLOBALES
CREATE  or alter VIEW [dbo].[secuenciasGlobales]
AS
WITH SecDisponibles AS 
( 
select t.SecSQL,s.current_value secActual, 
max(g.SecuFinal) - isnull(CAST(s.last_used_value AS int),0) restan 
from sis_globalSec g  
join sis_TipoNCF t on t.Codigo=g.idTipoNCF 
join sys.sequences s on s.name COLLATE SQL_Latin1_General_CP1_CI_AS = t.SecSQL 
where g.estado in (1,2) group by t.SecSQL,s.current_value,s.last_used_value  
) 
SELECT t.Auxiliar, t.Descripcion, t.SecSQL Prefijo, g.FVencimiento, g.Estado, d.restan, 
g.notificar FROM sis_TipoNCF t 
join SecDisponibles d ON d.SecSQL = t.SecSQL  
join sis_globalSec g on g.idTipoNCF=t.Codigo  
where d.secActual between g.SecuInicial and g.SecuFinal 
and t.Activo='1'  and g.estado <> 4 

GO
/****** Object:  View [dbo].[vFETablaDescuentosyRecargos]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE  or alter VIEW [dbo].[vFETablaDescuentosyRecargos] AS
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
/****** Object:  View [dbo].[vFETablaImpuestosAdicionales]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE  or alter VIEW [dbo].[vFETablaImpuestosAdicionales]  as 
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

 Where 0>1
GO
/****** Object:  View [dbo].[vFETablaPago]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFETablaPago] AS
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
    WHERE fp.MontoPago IS NOT NULL AND fp.MontoPago <> 0

   )


SELECT * FROM Pagos




GO
/****** Object:  View [dbo].[vFETotales]    Script Date: 20/09/2025 11:43:48 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE  or alter VIEW [dbo].[vFETotales] AS 	
	
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
			cxc.rncemisor,cxc.ncf as eNCF,cxc.documento as NumeroFacturaInterna,cxc.tipo as TipoDocumento,
			4 AS IndicadorFacturacion,
			'E' AS SiglasImpuesto, 1 as TipoCambio,
			sum(cxc.descuen) as MontoDescuento,
			sum(COALESCE(cxc.impuesto, 0 )) as MontoImpuesto,
			sum(COALESCE(cxc.Monto, 0 )) AS MontoTotal
		from  cxcmovi1 cxc WITH (NOLOCK)
		where cxc.estadofiscal is not null
		group by cxc.rncemisor,cxc.ncf,cxc.documento,cxc.tipo


		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF,NumeroFacturaInterna, TipoDocumento, TipoCambio
GO
EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPane1', @value=N'[0E232FF0-B466-11cf-A24F-00AA00A3EFFF, 1.00]
Begin DesignProperties = 
   Begin PaneConfigurations = 
      Begin PaneConfiguration = 0
         NumPanes = 4
         Configuration = "(H (1[40] 4[20] 2[20] 3) )"
      End
      Begin PaneConfiguration = 1
         NumPanes = 3
         Configuration = "(H (1 [50] 4 [25] 3))"
      End
      Begin PaneConfiguration = 2
         NumPanes = 3
         Configuration = "(H (1 [50] 2 [25] 3))"
      End
      Begin PaneConfiguration = 3
         NumPanes = 3
         Configuration = "(H (4[30] 2[40] 3) )"
      End
      Begin PaneConfiguration = 4
         NumPanes = 2
         Configuration = "(H (1 [56] 3))"
      End
      Begin PaneConfiguration = 5
         NumPanes = 2
         Configuration = "(H (2[66] 3) )"
      End
      Begin PaneConfiguration = 6
         NumPanes = 2
         Configuration = "(H (4 [50] 3))"
      End
      Begin PaneConfiguration = 7
         NumPanes = 1
         Configuration = "(V (3))"
      End
      Begin PaneConfiguration = 8
         NumPanes = 3
         Configuration = "(H (1[56] 4[18] 2) )"
      End
      Begin PaneConfiguration = 9
         NumPanes = 2
         Configuration = "(H (1 [75] 4))"
      End
      Begin PaneConfiguration = 10
         NumPanes = 2
         Configuration = "(H (1[66] 2) )"
      End
      Begin PaneConfiguration = 11
         NumPanes = 2
         Configuration = "(H (4 [60] 2))"
      End
      Begin PaneConfiguration = 12
         NumPanes = 1
         Configuration = "(H (1) )"
      End
      Begin PaneConfiguration = 13
         NumPanes = 1
         Configuration = "(V (4))"
      End
      Begin PaneConfiguration = 14
         NumPanes = 1
         Configuration = "(V (2) )"
      End
      ActivePaneConfig = 14
   End
   Begin DiagramPane = 
      PaneHidden = 
      Begin Origin = 
         Top = 0
         Left = 0
      End
      Begin Tables = 
         Begin Table = "f"
            Begin Extent = 
               Top = 6
               Left = 38
               Bottom = 136
               Right = 347
            End
            DisplayFlags = 280
            TopColumn = 0
         End
         Begin Table = "ef"
            Begin Extent = 
               Top = 138
               Left = 38
               Bottom = 234
               Right = 208
            End
            DisplayFlags = 280
            TopColumn = 0
         End
      End
   End
   Begin SQLPane = 
   End
   Begin DataPane = 
      PaneHidden = 
      Begin ParameterDefaults = ""
      End
   End
   Begin CriteriaPane = 
      PaneHidden = 
      Begin ColumnWidths = 11
         Column = 1440
         Alias = 900
         Table = 1170
         Output = 720
         Append = 1400
         NewValue = 1170
         SortType = 1350
         SortOrder = 1410
         GroupBy = 1350
         Filter = 1350
         Or = 1350
         Or = 1350
         Or = 1350
      End
   End
End
' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'vMonitorSentences'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPaneCount', @value=1 , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'vMonitorSentences'
GO
