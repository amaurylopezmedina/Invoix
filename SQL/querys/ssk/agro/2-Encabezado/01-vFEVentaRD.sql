--CREATE OR ALTER VIEW   vFEVentaRD AS 
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
  '' as EquipoImpresion

FROM
  dbo.Transa01 AS tr WITH   (NOLOCK)
 LEFT OUTER JOIN dbo.cliente AS c WITH (NOLOCK) ON tr.cliente = c.cliente
 LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor  = e.rnc 
 LEFT OUTER JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)  
 LEFT OUTER JOIN dbo.zona as z  WITH (NOLOCK) on z.zona = tr.zona
 --LEFT OUTER JOIN dbo.ruta as r  WITH (NOLOCK) on r.ruta = tr.ruta
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.RNCEmisor = TR.RNCEmisor and Totales.eNCF = tr.ncf
 CROSS JOIN AmbienteInfo AI 
WHERE
  tr.tipo IN ('03', '04')
  AND tr.ncf IS NOT NULL
  AND tr.ncf <> ''
  AND tr.EstadoFiscal IS NOT NULL
  AND SUBSTRING(tr.ncf, 1, 1) = 'E'
  AND tr.RNCEmisor IS NOT NULL


