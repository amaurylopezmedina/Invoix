CREATE OR ALTER VIEW   vFEEncabezado AS 

--Ventas en Pesos
Select * from vFEVentaRD

union all

--Ventas en Dolares
Select * from vFEVentaUS

union all

--Devoluciones a Contado
Select * from vFEDevCORD

union all

--Decoluciones a Credito
Select * from vFEDevCRRD


/*
union all

Select * from vFENCDIRD 
*/

Union all

--Gastos Menores

Select * from vFEGASMENCC

union all

Select * from vFEGASMENCXP

--Compras Informales

union all

Select * from vFEEncPI





