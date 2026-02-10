
CREATE OR ALTER VIEW vFETablaDescuentosyRecargos AS
 SELECT 
        td.numero as NumeroFacturaInterna,
		SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
		SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
		tr.ncf AS eNCF,
		tr.RNCEmisor,
        1 as NumeroLineaDoR,
        null as TipoAjuste,
        null as IndicadorNorma1007,
        (trim(cast((td.cantidad *-1 )as varchar(10)))+' '+trim(p.descrip)+' PRECIO '+cast( (td.precio *-1) as varchar(10))+' TOTAL:'+cast( (td.monto1 *-1) as varchar(20)))  as DescripcionDescuentooRecargo,
        '$' as TipoValor,
        null as ValorDescuentooRecargo,
        (td.monto1 *-1) as MontoDescuentooRecargo,
        null as MontoDescuentooRecargoOtraMoneda,
        '4' as IndicadorFacturacionDescuentooRecargo

 from tradetalle td WITH (NOLOCK)

 LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
 LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo

where td.precio < 0 and tr.EstadoFiscal is not null