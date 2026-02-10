--Devoluciones a credito (03) en cxcmovi1 y (05) en transa01

create or alter view VFEDetalleCXCMovi1Devolucion as
SELECT
  td.orden AS NumeroLinea,
  td.numero AS NumeroFacturaInterna,
  td.tipo AS TipoDocumento,
  SUBSTRING(cxc.ncf, 2, 2) AS TipoECF,
  SUBSTRING(cxc.ncf, 1, 1) AS TipoECFL,
  cxc.ncf AS eNCF,
  cxc.RNCEmisor,
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
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN td.precio * 1
      ELSE td.precio * cxc.tasa
    END
  ) AS PrecioUnitarioItem,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN td.montodesc * 1
      ELSE td.montodesc * cxc.tasa
    END
  ) AS DescuentoMonto,
  td.itbis AS TasaITBIS,
  (
    SELECT
      itbisenprecio
    FROM
      dbo.empresa AS e1
    WHERE
      (cxc.RNCEmisor = rnc)
  ) AS IndicadorMontoGravado,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN td.montoitbis * 1
      ELSE td.montoitbis * cxc.tasa
    END
  ) AS MontoITBIS,
  td.descuen AS TasaDescuento,
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
  COALESCE(cxc.tasa, 0.00) AS TipoCambio,
  td.montoitbis AS MontoITBISOtraMoneda,
  td.precio AS PrecioOtraMoneda,
  td.montodesc AS DescuentoOtraMoneda,
  NULL AS MontoRecargoOtraMoneta,
  td.monto1 AS MontoItemOtraMoneda,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN td.monto1 * 1
      ELSE td.monto1 * cxc.tasa
    END
  ) AS MontoItem,
  cxc.EstadoFiscal,
  cxc.Trackid,
  cxc.FechaFirma,
  cxc.CodigoSeguridad,
  cxc.Estadoimpresion,
  null as ConteoImpresiones
FROM
  dbo.tradetalle AS td
  LEFT OUTER JOIN dbo.producto AS p ON p.producto = td.producto
  LEFT OUTER JOIN dbo.impuesto AS i ON i.impuesto = p.impuesto
  LEFT OUTER JOIN dbo.cxcmovi1 AS cxc ON cxc.documento = td.numero  AND cxc.tipomovi = '03'
  AND td.tipo = '05'
WHERE
  (td.tipo IN ('05'))
  AND (cxc.EstadoFiscal IS NOT NULL)

