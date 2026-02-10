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

	where numero in ('B00000511052','B00000511051')
	GROUP BY numero, tipo 


--sELECT * FROM TRANSA01