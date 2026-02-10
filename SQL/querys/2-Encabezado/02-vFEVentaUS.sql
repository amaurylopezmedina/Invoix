--CREATE OR ALTER VIEW   vFEVentaUS AS 
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
  (Totales.MontoGravadoTotal * COALESCE(tr.tasa, 1.00))  as  MontoGravadoTotal,
  (Totales.MontoGravadoI18 * COALESCE(tr.tasa, 1.00))  as MontoGravadoI1, --18
  (Totales.MontoGravadoI16 * COALESCE(tr.tasa, 1.00))   as MontoGravadoI2, -- 16
  (Totales.MontoGravadoIEX * COALESCE(tr.tasa, 1.00))   as MontoGravadoI3,  -- Exportacion
  (Totales.MontoExento * COALESCE(tr.tasa, 1.00)) as MontoExento,
  (Totales.ITBIS1 * COALESCE(tr.tasa, 1.00))  ITBIS1,
  (Totales.ITBIS2 * COALESCE(tr.tasa, 1.00))  ITBIS2,
  (Totales.ITBIS3 * COALESCE(tr.tasa, 1.00))  ITBIS3,
  (Totales.TotalITBIS * COALESCE(tr.tasa, 1.00))  TotalITBIS,
  (Totales.TotalITBIS1 * COALESCE(tr.tasa, 1.00))  TotalITBIS1,
  (Totales.TotalITBIS2 * COALESCE(tr.tasa, 1.00))  TotalITBIS2,
  (Totales.TotalITBIS3 * COALESCE(tr.tasa, 1.00))  TotalITBIS3,
  (Totales.IndicadorMontoGravadoI18 * COALESCE(tr.tasa, 1.00))  IndicadorMontoGravadoI18,
  (Totales.IndicadorMontoGravadoI16 * COALESCE(tr.tasa, 1.00))  IndicadorMontoGravadoI16,
  (Totales.IndicadorMontoGravadoINF * COALESCE(tr.tasa, 1.00))  IndicadorMontoGravadoINF,
  (Totales.IndicadorMontoGravadoIEX * COALESCE(tr.tasa, 1.00))  IndicadorMontoGravadoIEX,
  (Totales.IndicadorMontoGravadoIE * COALESCE(tr.tasa, 1.00))  IndicadorMontoGravadoIE,

  NULL AS MontoImpuestoAdicional,

  --Seccion Totales Otra Moneda
  --Indicacion de Tipo de Moneda
  'USD' AS TipoMoneda,
  --Descripcion del tipo de moneda
  'DOLAR ESTADOUNIDENSE' AS TipoMonedaL,
  --Tipo de Cambio (Tasa)
  tr.tasa AS TipoCambio,
  --Montos expresado en otra Moneda
  Totales.MontoGravadoTotal as MontoGravadoTotalOtraMoneda,
  Totales.MontoGravadoI18 as MontoGravado1OtraMoneda,
  Totales.MontoGravadoI16 as MontoGravado2OtraMoneda,
  Totales.MontoGravadoIEX as MontoGravado3OtraMoneda,
  Totales.MontoExento as MontoExentoOtraMoneda,
  Totales.TotalITBIS as TotalITBISOtraMoneda,
  Totales.TotalITBIS1 as TotalITBIS1OtraMoneda,
  Totales.TotalITBIS2 as TotalITBIS2OtraMoneda,
  Totales.TotalITBIS3 as TotalITBIS3OtraMoneda,
  NULL AS MontoImpuestoAdicionalOtraMoneda,
  tr.monto AS MontoTotalOtraMoneda,

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
        WHEN SUBSTRING(TR.ncf, 2, 2) = '32' AND (TR.monto * COALESCE(tr.tasa, 1.00)) < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&MontoTotal=', round((TR.monto * COALESCE(tr.tasa, 1.00)),2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(TR.CodigoSeguridad))
            )
        WHEN SUBSTRING(TR.ncf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(TR.rncemisor),
                '&ENCF=', TRIM(TR.ncf),
                '&FechaEmision=', dbo.FNFechaDMY(TR.fecha),
                '&MontoTotal=', round((TR.monto * COALESCE(tr.tasa, 1.00)),2),
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
                '&MontoTotal=', round((TR.monto * COALESCE(tr.tasa, 1.00)),2),
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
  CASE
      --WHEN COALESCE(trim(tr.observa1), '') <> '' THEN tr.observa1 
      WHEN COALESCE(trim(e.nota), '') <> '' THEN e.nota 
      ELSE ''
    END
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
 LEFT OUTER JOIN Totales as Totales  WITH (NOLOCK) on Totales.numero = TR.numero and Totales.tipo = tr.tipo
 CROSS JOIN AmbienteInfo AI 
WHERE
  (tr.tipo IN ('33', '34'))
  AND (tr.ncf IS NOT NULL)
  AND (tr.ncf <> '')
  AND (tr.EstadoFiscal IS NOT NULL)


