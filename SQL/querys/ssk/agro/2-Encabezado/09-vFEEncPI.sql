
create or alter view vFEEncPI as

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
   LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = cxp.RNCEmisor and Totales.eNCF = cxp.ncf
  CROSS JOIN AmbienteInfo AI
WHERE
  (cxp.tipomovi IN ('07'))
  AND (cxp.informal=1)
  AND (cxp.ncf IS NOT NULL)
  AND (cxp.ncf <> '')
  AND (cxp.EstadoFiscal IS NOT NULL)
  AND SUBSTRING(cxp.ncf, 1, 1) = 'E'
  AND cxp.RNCEmisor IS NOT NULL





