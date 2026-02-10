Create or alter view  vmonitorsentences as

SELECT        
CAST(f.FechaEmision AS DATE) AS FechaEmision, 
f.NumeroFacturaInterna AS Factura, 
f.TipoPagoL AS TipoVenta, 
f.TipoECF, 
f.eNCF, f.EstadoFiscal, 
ef.Descrip AS DescripcionEstadoFiscal, 
f.EstadoImpresion, 
LEFT(f.NumeroFacturaInterna, 1) AS Caja, 
f.URLQR AS URLC, 
f.ResultadoEstadoFiscal, 
f.MontoTotal AS MontoFacturado, 
f.TotalITBIS AS ITBISFacturado, 
f.MontoDGII, 
f.MontoITBISDGII, 
f.RNCEmisor
FROM  dbo.vFEEncabezado AS f 
     LEFT OUTER JOIN dbo.EstadoFiscal AS ef ON f.EstadoFiscal = ef.estado