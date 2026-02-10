SELECT td.numero, td.fecha, td.tipo, cxc.RNCEmisor, cxc.ncf, COALESCE (cxc.tasa, 1.00) AS tasa, td.itbis,
(SELECT itbisenprecio  FROM    dbo.empresa AS e1  WHERE (cxc.RNCEmisor = rnc)) AS IndicadorMontoGravado, 

(CASE WHEN (SELECT itbisenprecio FROM    dbo.empresa AS e1 WHERE (cxc.RNCEmisor = e1.rnc)) = 0 THEN SUM(CASE WHEN td.itbis <> 0 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * cxc.tasa END) ELSE 0.00 END) WHEN
(SELECT itbisenprecio FROM dbo.empresa AS e1  WHERE (cxc.RNCEmisor = e1.rnc)) = 1 THEN SUM(CASE WHEN td.itbis <> 0 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * cxc.tasa END) ELSE 0.00 END) 
- SUM(CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.montoitbis * 1 ELSE td.montoitbis * cxc.tasa END) END) AS MontoGravadoTotal, 

(CASE WHEN (SELECT itbisenprecio FROM    dbo.empresa AS e1 WHERE (cxc.RNCEmisor = e1.rnc)) = 0 AND td.itbis = 18 THEN SUM(CASE WHEN td.itbis = 18 THEN 
(CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * cxc.tasa END) ELSE 0.00 END) WHEN
(SELECT itbisenprecio FROM    dbo.empresa AS e1 WHERE (cxc.RNCEmisor = e1.rnc)) = 1 AND td.itbis = 18 THEN SUM(CASE WHEN td.itbis = 18 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * cxc.tasa END) ELSE 0.00 END) - SUM(CASE WHEN COALESCE (cxc.tasa, 1.00) 
= 1 THEN td.montoitbis * 1 ELSE td.montoitbis * cxc.tasa END) ELSE 0.00 END) AS MontoGravadoI1, 

(CASE WHEN (SELECT itbisenprecio FROM    dbo.empresa AS e1 WHERE (cxc.RNCEmisor = e1.rnc)) = 0 AND td.itbis = 16 THEN SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * cxc.tasa END) ELSE 0.00 END) WHEN
(SELECT itbisenprecio FROM    dbo.empresa AS e1 WHERE (cxc.RNCEmisor = e1.rnc)) = 1 AND td.itbis = 16 THEN SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * cxc.tasa END) ELSE 0.00 END) - SUM(CASE WHEN COALESCE (cxc.tasa, 1.00) 
= 1 THEN td.montoitbis * 1 ELSE td.montoitbis * cxc.tasa END) ELSE 0.00 END) AS MontoGravadoI2, 

SUM(CASE WHEN td.itbis = 0 THEN 0.00 ELSE 0.00 END) AS MontoGravadoI3, 

SUM(CASE WHEN td.itbis = 0 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN td.monto1 * COALESCE (cxc.tasa, 1.00)  ELSE td.monto1 * cxc.tasa END) ELSE null END) AS MontoExento, 

MAX(CASE WHEN td.itbis = 18 THEN td.itbis ELSE null END) AS ITBIS1, 
MAX(CASE WHEN td.itbis = 16 THEN td.itbis ELSE null END) AS ITBIS2, 

MAX(CASE WHEN td.itbis = 0 THEN td.itbis ELSE null END) AS ITBIS3, 

 SUM((CASE WHEN COALESCE (cxc.tasa, 1) = 1 THEN td.montoitbis * COALESCE (cxc.tasa, 1) ELSE td.montoitbis * cxc.tasa END)) AS TotalITBIS, 

 SUM(CASE WHEN td.itbis = 18 THEN td.montoitbis * COALESCE (cxc.tasa, 1) ELSE null END) AS TotalITBIS1, 

SUM(CASE WHEN td.itbis = 16 THEN td.montoitbis * COALESCE (cxc.tasa, 1) ELSE null END) AS TotalITBIS2, 

SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE null END) AS TotalITBIS3, 

MAX(CASE WHEN td.itbis = 18 THEN 1 ELSE 0 END) AS IndicadorMontoGRabadoI18, 

MAX(CASE WHEN td.itbis = 16 THEN 1 ELSE 0 END) AS IndicadorMontoGRabadoI16, 

MAX(CASE WHEN td.itbis = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGRabadoI0, 

SUM(CASE WHEN td.itbis <> 0 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN 1 ELSE td.monto1 END) ELSE 0.00 END) AS MontoGravadoTotalOtraMoneda,

SUM(CASE WHEN td.itbis = 18 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN 1 ELSE td.monto1 END) ELSE 0.00 END) AS MontoGravadoI1OtraMoneda, 

SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN 1 ELSE td.monto1 END) ELSE 0.00 END) AS MontoGravadoI2OtraMoneda, 
SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) AS MontoGravadoI3OtraMoneda, 
SUM(CASE WHEN td.itbis = 0 THEN (CASE WHEN COALESCE (cxc.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END) ELSE 0.00 END) AS MontoExentoOtraMoneda, 
SUM((CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN 0 ELSE td.montoitbis END)) AS TotalITBISOtraMoneda, 
SUM(CASE WHEN td.itbis = 18 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) = 1 THEN 0 ELSE td.montoitbis END) ELSE 0.00 END) AS TotalITBIS1OtraMoneda, 
SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (cxc.tasa, 1.00) 
= 1 THEN 0 ELSE td.montoitbis END) ELSE 0.00 END) AS TotalITBIS2OtraMoneda, 
SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) AS TotalITBIS3OtraMoneda

                 FROM    dbo.tradetalle AS td LEFT OUTER JOIN
                              dbo.cxcmovi1 AS cxc ON cxc.documento = td.numero AND  td.tipo = '05' and cxc.tipomovi ='03'
							  Where estadofiscal is not null
                 GROUP BY td.numero, td.fecha, td.tipo, cxc.RNCEmisor, cxc.ncf, COALESCE (cxc.tasa, 1.00), td.itbis






