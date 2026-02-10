
CREATE   PROCEDURE [dbo].[sp_FEVentaContadoRD]
    @RNCEmisor VARCHAR(20) = NULL,
    @ENCF VARCHAR(20) = NULL,
    @Numero VARCHAR(20) = NULL,
    @Tipo VARCHAR(2) = NULL,
    @Desde DATETIME = NULL,
    @Hasta DATETIME = NULL
AS
BEGIN
    SET NOCOUNT ON;

    /* Facturas electrónicas (ECF) de CONTADO (tipo '03')
       - Incluye todos los campos del modelo original
       - TipoCambio = ISNULL(NULLIF(tr.tasa,0),1)
       - Filtros opcionales por RNCEmisor, ENCF, Numero/Tipo y rango @Desde/@Hasta
       - Ordenado por tr.fechacreacion DESC
       - Lecturas rápidas con NOLOCK
    */

    WITH
    AmbienteInfo AS (
        SELECT 
            A.AMBIENTE AS AMBIENTE,
            A.DESCRIP  AS DESCRIP,
            ISNULL(LTRIM(RTRIM(A.RUTA)), '') AS RUTA
        FROM FEAmbiente AS A WITH (NOLOCK)
        WHERE A.RUTA IS NOT NULL AND LTRIM(RTRIM(A.RUTA)) <> ''
    ),
    NotaCaja AS (
        SELECT LTRIM(RTRIM(caja)) AS caja, LTRIM(RTRIM(nota)) AS nota
        FROM caja WITH (NOLOCK)
    )
    SELECT
      /* Identificación */
      tr.numero AS NumeroFacturaInterna,
      tr.tipo AS TipoDocumento,
      SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
      SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
      tn.Descripcion AS TipoECFL1,
      tn.Descripcion,
      tr.idfe,
      tn.Auxiliar,
      'TRANSA01' AS Tabla,
      'rncemisor' AS campo1,
      'ncf' AS campo2,
      LTRIM(RTRIM(tr.ncf)) AS eNCF,

      /* Vencimientos / términos */
      tr.FVencimientoNCF AS FechaVencimientoSecuencia,
      tr.vence AS FechaLimitePago,
      0 AS TerminoPagoN,
      '' AS TerminoPago,

      /* Operativo */
      tr.almacen AS Almacen,
      0 AS IndicadorNotaCredito,
      e.itbisenprecio AS IndicadorMontoGravado ,
      '01' AS TipoIngresos,
      1 AS TipoPago,
      'CONTADO' AS TipoPagoL,
      NULL AS TipoCuentaPago,
      NULL AS NumeroCuentaPago,
      NULL AS BancoPago,
      NULL AS FechaDesde,
      NULL AS FechaHasta,
      NULL AS TotalPaginas,

      /* Emisor */
      REPLACE(tr.RNCEmisor, '-', '') AS RNCEmisor,
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
      LTRIM(RTRIM(ve.tele)) AS TelefonoEmisor2,
      CAST('' AS CHAR(1)) AS TelefonoEmisor3,
      LTRIM(RTRIM(tr.vendedor)) AS CodigoVendedor,
      LTRIM(RTRIM(tr.pedido)) AS NumeroPedidoInterno,
      CAST('' AS CHAR(1)) AS ZonaVenta,
      '' AS RutaVenta,
      CAST('' AS CHAR(1)) AS InformacionAdicionalEmisor,

      /* Comprador */
      tr.fecha AS FechaEmision,
      CASE
        WHEN ISNULL (LTRIM(RTRIM(tr.CEDULA)), '') = '' THEN REPLACE(ISNULL(c.rnc1,''), '-', '')
        ELSE REPLACE(LTRIM(RTRIM(tr.CEDULA)), '-', '')
      END AS RNCComprador,
      NULL AS IdentificadorExtranjero,
      CASE
        WHEN ISNULL(LTRIM(RTRIM(c.Nombre)), '') = '' THEN ISNULL(LTRIM(RTRIM(tr.nombre)),'CLIENTE GENERICO')
        ELSE LTRIM(RTRIM(c.Nombre))
      END AS RazonSocialComprador,
      '' AS ContactoComprador,
      '' AS CorreoComprador,
      c.Dire AS DireccionComprador,
      CAST('' AS CHAR(1)) AS MunicipioComprador, 
      CAST('' AS CHAR(1)) AS ProvinciaComprador,
      CAST('' AS CHAR(1)) AS PaisComprador,
      NULL AS FechaEntrega,
      CAST('' AS CHAR(1)) AS ContactoEntrega,
      LTRIM(RTRIM(tr.dire)) AS DireccionEntrega,
      tr.Tele AS TelefonoAdicional,
      NULL AS FechaOrdenCompra,
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
      NULL AS RutaTransporte,
      '' AS ZonaTransporte,
      NULL AS NumeroAlbaran,
      LTRIM(RTRIM(ve.nombre)) AS NombreVendedor,

      /* Impuestos adicionales */
      NULL AS MontoImpuestoAdicional,

      /* Moneda */
      'DOP' AS TipoMoneda,
      'PESOS DOMINICANO' AS TipoMonedaL,
      ISNULL(NULLIF(tr.tasa,0),1) AS TipoCambio,
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

      /* Totales */
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

      /* Nota de crédito (placeholders) */
      CAST('' AS CHAR(1)) AS NCFModificado,
      CAST('' AS CHAR(1)) as RNCOtroContribuyente,
      NULL AS FechaNCFModificado,
      NULL AS CodigoModificacion,
      CAST('' AS CHAR(1)) AS NumeroDocumentoNCFModificado,
      0 AS MontoNCFModificado,
      0 AS AbonoNCFModificado,
      0 AS DescuentoNCFModificado,
      0 AS PendienteNCFModificado,
      CAST('' AS CHAR(1)) AS RazonModificacion,

      /* ECF metadata */
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

      /* URL del QR */
      CASE
        WHEN SUBSTRING(LTRIM(RTRIM(tr.ncf)), 2, 2) = '32' AND ISNULL(tr.monto,0) < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do',
                '/ConsultaTimbreFC?RncEmisor=', LTRIM(RTRIM(tr.rncemisor)),
                '&ENCF=', LTRIM(RTRIM(tr.ncf)),
                '&MontoTotal=', ROUND(ISNULL(tr.monto,2),2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](LTRIM(RTRIM(ISNULL(tr.CodigoSeguridad,''))))
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do',
                '/ConsultaTimbre?RncEmisor=', LTRIM(RTRIM(tr.rncemisor)),
                '&ENCF=', LTRIM(RTRIM(tr.ncf)),
                '&FechaEmision=', ISNULL(dbo.FNFechaDMY(tr.fecha), ''),
                '&MontoTotal=', ROUND(ISNULL(tr.monto,2),2),
                '&FechaFirma=', REPLACE(LTRIM(RTRIM(ISNULL(tr.FechaFirma, ''))), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](LTRIM(RTRIM(ISNULL(tr.CodigoSeguridad,''))))
            )
      END  AS URLQR ,

      /* Observaciones y tracking */
      ISNULL(tr.observa, '') AS Observaciones,
      tr.creado AS Creadopor,
      tr.usuario AS Usuario,
      '' AS ModificadoPor,
      tr.usuario as Cajero,

      /* Nota permanente */
      CONCAT_WS('|',
          LTRIM(RTRIM(ISNULL(e.nota, ''))),
          LTRIM(RTRIM(ISNULL(tr.OBSERVA3, ''))),
          LTRIM(RTRIM(ISNULL(nc.nota, '')))
      ) AS NotaPermanente,  
      tr.Descrip1 as NotaPago,
      '' as NotaAntesDeProductos,
      tr.pccreado as EquipoImpresion

    FROM dbo.Transa01 AS tr WITH (NOLOCK)
    LEFT JOIN dbo.cliente     AS c WITH (NOLOCK) ON c.cliente = tr.cliente
    LEFT JOIN dbo.empresa     AS e WITH (NOLOCK) ON REPLACE(e.rnc, '-', '') = REPLACE(tr.RNCEmisor, '-', '')
    LEFT JOIN dbo.sis_TipoNCF AS tn WITH (NOLOCK) ON tn.Codigo = SUBSTRING(tr.ncf, 2, 2)
    LEFT JOIN NotaCaja        AS nc WITH (NOLOCK) ON nc.caja = SUBSTRING(tr.numero, 1, 1)
    LEFT JOIN vendedor        AS ve WITH (NOLOCK) ON LTRIM(RTRIM(ve.vendedor)) = LTRIM(RTRIM(tr.vendedor))
    LEFT JOIN AmbienteInfo AS AI WITH (NOLOCK) ON e.ambiente = AI.ambiente
    WHERE
        tr.tipo = '03'
        AND SUBSTRING(tr.ncf, 1, 1) = 'E'
        AND tr.ncf IS NOT NULL AND LTRIM(RTRIM(tr.ncf)) <> ''
        AND tr.EstadoFiscal IS NOT NULL
        AND (@RNCEmisor IS NULL OR REPLACE(tr.RNCEmisor, '-', '') = REPLACE(@RNCEmisor, '-', ''))
        AND (@ENCF IS NULL OR tr.ncf = @ENCF)
        AND (@Numero IS NULL OR (tr.numero = @Numero AND (@Tipo IS NULL OR tr.tipo = @Tipo)))
        AND (@Desde IS NULL OR CAST(tr.fechacreacion AS DATE) >= CAST(@Desde AS DATE))
        AND (@Hasta IS NULL OR CAST(tr.fechacreacion AS DATE) <= CAST(@Hasta AS DATE))
    ORDER BY tr.fechacreacion DESC;
END
