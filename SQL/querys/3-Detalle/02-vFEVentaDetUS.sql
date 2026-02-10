create or alter view vFEDetalleTransa01 as
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
  '43' AS UnidadMedida,
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
      ELSE td.monto1 * tr.tasa
    END
  ) AS MontoItem,
  p.NotaImpresion
FROM
  dbo.tradetalle AS td
  LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
  LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo
  LEFT OUTER JOIN dbo.empresa AS e WITH (NOLOCK) ON tr.RNCEmisor = e.rnc
WHERE
  (td.tipo IN ('33', '34'))
  AND (tr.EstadoFiscal IS NOT NULL) 

