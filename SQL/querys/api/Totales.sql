Create or Alter View vFETotales AS 	
	
	SELECT 
		RNCEmisor,
		eNCF,
		TipoCambio,
		(SUM(MontoTotal)) * TipoCambio as MontoTotal,
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) * TipoCambio as MontoGravadoTotal,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoExento,
		SUM(MontoImpuesto)* TipoCambio as TotalITBIS,
		SUM(MontoDescuento) * TipoCambio as MontoDescuentoTotal,

		MAX(CASE WHEN IndicadorFacturacion = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoINF,
		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIEX,
		MAX(CASE WHEN IndicadorFacturacion = 4 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoIE,

		SUM(CASE WHEN IndicadorFacturacion = 0 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoINF,
		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI18,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI16,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIEX,
		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoIE,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 18 ELSE 0 END) AS ITBIS1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 16 ELSE 0 END) AS ITBIS2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 0 ELSE 0 END) AS ITBIS3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END)* TipoCambio AS TotalITBIS3,

		MAX(CASE WHEN IndicadorFacturacion = 1 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI1,
		MAX(CASE WHEN IndicadorFacturacion = 2 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI2,
		MAX(CASE WHEN IndicadorFacturacion = 3 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI3,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI1,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI2,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)* TipoCambio AS MontoGravadoI3,

		0 AS MontoImpuestoAdicional,

		--Otra Moneda
		(SUM(MontoTotal)-sum(MontoImpuesto)-SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END)) as MontoGravadoTotalOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoTotal-MontoImpuesto ELSE 0 END) AS MontoGravado2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoTotal-MontoImpuesto ELSE 0 END)  AS MontoGravado3OtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 4 THEN MontoTotal-MontoImpuesto ELSE 0 END) as MontoExentoOtraMoneda,

		SUM(MontoImpuesto) as TotalITBISOtraMoneda,

		SUM(CASE WHEN IndicadorFacturacion = 1 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS1OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 2 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS2OtraMoneda,
		SUM(CASE WHEN IndicadorFacturacion = 3 THEN MontoImpuesto ELSE 0 END) AS TotalITBIS3OtraMoneda,

		0 AS MontoImpuestoAdicionalOtraMoneda,

	    (SUM(MontoTotal)) AS MontoTotalOtraMoneda

	FROM
		(
			Select 
				RNCEmisor,encf,	
				CASE
					WHEN SUBSTRING(encf, 2, 2)=46 THEN 3
					ELSE IndicadorFacturacion
				END AS IndicadorFacturacion, 
				imp.Siglas,
				1 as TipoCambio,
				sum(DescuentoMonto) as MontoDescuento,
				--sum((CantidadItem *PrecioUnitarioItem )*(imp.tasa/100)) as MontoImpuesto,
				sum((MontoItem)*(imp.tasa/100)) as MontoImpuesto,
				sum(COALESCE(MontoItem, 0 )) AS MontoTotal 
			from fedetalle det WITH (NOLOCK)
			LEFT OUTER JOIN dbo.ITBISDGII AS imp WITH (NOLOCK) ON imp.codigo = det.IndicadorFacturacion
			group by RNCEmisor, encf, IndicadorFacturacion, Siglas

		) AS SubConsulta
	GROUP BY RNCEmisor,eNCF, TipoCambio