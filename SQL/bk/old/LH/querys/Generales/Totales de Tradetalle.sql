declare @itbisenprecio bit
select @itbisenprecio=itbisenprecio from empresa
SELECT td.numero, td.tipo, max(isnull(tr.tasa, 1)) as tasa, 

--MontoTotal
SUM(CASE WHEN @itbisenprecio = 0 THEN CASE WHEN td.itbis <> 0 THEN CASE WHEN COALESCE (tr.tasa, 1.00) 
= 1 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END ELSE 0.00 END WHEN @itbisenprecio = 1 THEN CASE WHEN td.itbis <> 0 THEN CASE WHEN COALESCE (tr.tasa, 1.00) 
= 1 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END ELSE 0.00 END - CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN td.montoitbis * 1 ELSE td.montoitbis * tr.tasa END END) AS MontoGravadoTotal,

--MontoGravadoI1
SUM(CASE WHEN @itbisenprecio = 0 AND 
td.itbis = 18 THEN CASE WHEN td.itbis = 18 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END ELSE 0.00 END WHEN @itbisenprecio = 1 AND td.itbis = 18 THEN CASE WHEN td.itbis = 18 THEN CASE WHEN COALESCE (tr.tasa, 
1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END ELSE 0.00 END - CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN td.montoitbis * 1 ELSE td.montoitbis * tr.tasa END ELSE 0.00 END) AS MontoGravadoI1,

--MontoGravadoI2
SUM(CASE WHEN @itbisenprecio = 0 AND td.itbis = 16 THEN CASE WHEN td.itbis = 16 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END ELSE 0.00 END WHEN @itbisenprecio = 1 AND td.itbis = 16 THEN CASE WHEN td.itbis = 16 THEN CASE WHEN COALESCE (tr.tasa, 
1.00) = 1 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END ELSE 0.00 END - CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN td.montoitbis * 1 ELSE td.montoitbis * tr.tasa END ELSE 0.00 END) AS MontoGravadoI2,

--MontoGravadoI3
SUM(CASE WHEN td.itbis = 0 THEN 0.00 ELSE 0.00 END) AS MontoGravadoI3,

-- MontoExento
 SUM(CASE WHEN td.itbis = 0 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN td.monto1 * COALESCE (tr.tasa, 1.00) ELSE td.monto1 * tr.tasa END ELSE NULL END) AS MontoExento,
 
 -- 18% si existen prodcutos grabados con este impuesto
MAX(CASE WHEN td.itbis = 18 THEN td.itbis ELSE 0 END) AS ITBIS1,

 -- 16% si existen prodcutos grabados con este impuesto
MAX(CASE WHEN td.itbis = 16 THEN td.itbis ELSE NULL END) AS ITBIS2,

 -- 0% si existen prodcutos grabados con este impuesto
MAX(CASE WHEN td.itbis = 0 THEN td.itbis ELSE NULL END) AS ITBIS3,

SUM(CASE WHEN COALESCE (tr.tasa, 1) = 1 THEN td.montoitbis * COALESCE (tr.tasa, 1) 
ELSE td.montoitbis * tr.tasa END) AS TotalITBIS, 

SUM(CASE WHEN td.itbis = 18 THEN td.montoitbis * COALESCE (tr.tasa, 1) ELSE NULL END) AS TotalITBIS1, 

SUM(CASE WHEN td.itbis = 16 THEN td.montoitbis * COALESCE (tr.tasa, 1) ELSE NULL END) AS TotalITBIS2, 
SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE NULL END) AS TotalITBIS3,

MAX(CASE WHEN td.itbis = 18 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI18, 

MAX(CASE WHEN td.itbis = 16 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI16,

MAX(CASE WHEN td.itbis = 0 THEN 1 ELSE 0 END) AS IndicadorMontoGravadoI0,
SUM(CASE WHEN td.itbis <> 0 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN 1 ELSE td.monto1 END ELSE 0.00 END) AS MontoGravadoTotalOtraMoneda, 
SUM(CASE WHEN td.itbis = 18 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN 1 ELSE td.monto1 END ELSE 0.00 END) AS MontoGravadoI1OtraMoneda, 
SUM(CASE WHEN td.itbis = 16 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN 1 ELSE td.monto1 END ELSE 0.00 END) AS MontoGravadoI2OtraMoneda,

SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) AS MontoGravadoI3OtraMoneda,

SUM(CASE WHEN td.itbis = 0 THEN CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END ELSE 0.00 END) AS MontoExentoOtraMoneda, 
SUM(CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN 0 ELSE td.montoitbis END) AS TotalITBISOtraMoneda,
SUM(CASE WHEN td.itbis = 18 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN 0 ELSE td.montoitbis END ELSE 0.00 END) AS TotalITBIS1OtraMoneda, 
SUM(CASE WHEN td.itbis = 16 THEN CASE WHEN COALESCE (tr.tasa, 1.00) = 1 THEN 0 ELSE td.montoitbis END ELSE 0.00 END) AS TotalITBIS2OtraMoneda, 
SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) AS TotalITBIS3OtraMoneda


FROM tradetalle td JOIN Transa01 tr on tr.numero=td.numero and tr.tipo=td.tipo 
WHERE  td.tipo IN ('03', '04', '33', '34', '17') AND (tr.EstadoFiscal IS NOT NULL) 
and isnull(tr.ncf,'') <>'' group by td.numero, td.tipo
