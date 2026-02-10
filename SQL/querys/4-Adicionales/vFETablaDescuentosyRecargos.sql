
CREATE OR ALTER VIEW vFETablaDescuentosyRecargos AS
 SELECT 
        td.numero as NumeroFacturaInterna,
		td.tipo as TipoDocumento,
		SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
		SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
		tr.ncf AS eNCF,
		tr.RNCEmisor,
        1 as NumeroLineaDoR,
        'D' as TipoAjuste,
        null as IndicadorNorma1007,
        'DESCUENTO A PRODUCTO'  as DescripcionDescuentooRecargo,
        '$' as TipoValor,
        null as ValorDescuentooRecargo,
		FORMAT(td.montodesc, '0.00') as MontoDescuentooRecargo,
        null as MontoDescuentooRecargoOtraMoneda,
        i.codigodgii as IndicadorFacturacionDescuentooRecargo

 from tradetalle td WITH (NOLOCK)

 LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
 LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
 LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo

 where  COALESCE(td.montodesc,0) > 0 and 0>0


