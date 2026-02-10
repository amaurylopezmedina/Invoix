/*Detalle de CXPMovi1*/

create or alter view VFEDetalleCXPMovi1 as

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
    i.codigodgii AS IndicadorFacturacion,
    i.Siglas AS SiglasImpuesto,
    i.Descrip AS DescripcionImpuesto,
    NULL AS IndicadorAgenteRetencionoPercepcion,
    cxp.itbisret AS MontoITBISRetenido,
    cxp.isr AS MontoISRRetenido,
    cxp.concepto NombreItem,
    1 AS IndicadorBienoServicio,
    NULL AS DescripcionItem,
    1 AS CantidadItem,
    '43' AS UnidadMedida,
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
    cxp.descuen AS DescuentoMonto,
    18 AS TasaITBIS,
    1 AS IndicadorMontoGravado,
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
    cxp.EstadoFiscal,
    cxp.Trackid,
    cxp.FechaFirma,
    cxp.CodigoSeguridad,
    cxp.Estadoimpresion,
    NULL AS ConteoImpresiones,
	'' as NotaImpresion 
FROM
    cxpmovi1 cxp
    LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = '02'
WHERE
    (cxp.tipomovi IN ('07'))
    AND (cxp.ncf IS NOT NULL)
    AND (cxp.ncf <> '')
    AND (cxp.EstadoFiscal IS NOT NULL)