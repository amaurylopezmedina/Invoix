
create or alter view vFEGASMENCC as

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
    null as idfe,
    MAX(tn.Auxiliar) as Auxiliar,
    'CAJACHICA' as Tabla,
    'rncemisor' as campo1,
    'ncf' as campo2,
	cc.ncf AS eNCF,
    MAX(cc.FVencimientoNCF) as FechaVencimientoSecuencia,
    NULL as FechaLimitePago,
    0 as TerminoPagoN,
    CAST('' AS CHAR(1)) as TerminoPago,
    ''as Almacen,
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
    max(cc.ResultadoEstadoFiscal) as ResultadoEstadoFiscal,
    max(cc.MontoDGII) as MontoDGII,
    max(cc.MontoITBISDGII) as MontoITBISDGII,
    MAX(CONCAT(
        'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?',
        'RncEmisor=', TRIM(cc.rncemisor),
        '&ENCF=', TRIM(cc.ncf),
        '&FechaEmision=', dbo.FNFechaDMY(cc.fecha),
        '&MontoTotal=', (cc.debito - cc.credito),
        '&FechaFirma=', REPLACE(TRIM(cc.FechaFirma), ' ', '%20'),
        '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](trim(cc.CodigoSeguridad))
    )) as URLQR,
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
