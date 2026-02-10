
create or alter view vFETablaImpuestosAdicionales  as 
 SELECT 
        td.numero as NumeroFacturaInterna,
		td.tipo as TipoDocumento,
		SUBSTRING(tr.ncf, 2, 2) AS TipoECF,
		SUBSTRING(tr.ncf, 1, 1) AS TipoECFL,
		tr.ncf AS eNCF,
		tr.RNCEmisor,
        null TipoImpuesto,
        null TasaImpuestoAdicional,
        null MontoImpuestoSelectivoConsumoEspecifico,
        null MontoImpuestoSelectivoConsumoAdvalorem,
        null OtrosImpuestosAdicionales
 
 from tradetalle td WITH (NOLOCK)

 LEFT OUTER JOIN dbo.producto AS p WITH (NOLOCK) ON p.producto = td.producto
 LEFT OUTER JOIN dbo.impuesto AS i WITH (NOLOCK) ON i.impuesto = p.impuesto
 LEFT OUTER JOIN dbo.Transa01 AS tr WITH (NOLOCK) ON tr.numero = td.numero AND tr.tipo = td.tipo

 Where 0>1 and 0>0