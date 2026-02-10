USE ASESYS
GO
Select   
	tr.rncemisor,tr.ncf as eNCF,td.numero as NumeroFacturaInterna,td.tipo as TipoDocumento,
	CASE
		WHEN SUBSTRING(tr.ncf, 2, 2)=46 THEN 3
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


USE FEPRD
GO

Select 
	RNCEmisor,encf,	
	CASE
		WHEN SUBSTRING(encf, 2, 2)=46 THEN 3
		ELSE IndicadorFacturacion
	END AS IndicadorFacturacion, 
	imp.Siglas,
	sum(DescuentoMonto) as MontoDescuento,
	--sum((CantidadItem *PrecioUnitarioItem )*(imp.tasa/100)) as MontoImpuesto,
	sum((MontoItem)*(imp.tasa/100)) as MontoImpuesto,
	sum(COALESCE(MontoItem, 0 )) AS MontoTotal 
from fedetalle det WITH (NOLOCK)
LEFT OUTER JOIN dbo.ITBISDGII AS imp WITH (NOLOCK) ON imp.codigo = det.IndicadorFacturacion
group by RNCEmisor, encf, IndicadorFacturacion, Siglas

Select * from ITBISDGII
