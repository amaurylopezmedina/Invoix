CREATE OR ALTER VIEW   vFEDevCRRD AS 
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
  null as idfe,
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
  cxc.documento AS NumeroDocumentoNCFModificado,
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
 LEFT OUTER JOIN dbo.Transa01 AS tr1 WITH (nolock) ON tr1.numero = cxc.documento and tr1.tipo = '04' -- Acceso a la factura a la que afecta
 CROSS JOIN AmbienteInfo AI 
WHERE
  (cxc.tipomovi IN ('03'))
  AND (cxc.ncf IS NOT NULL)
  AND (cxc.ncf <> '')
  AND (cxc.EstadoFiscal IS NOT NULL)

