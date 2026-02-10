CREATE OR ALTER VIEW   vFEEncabezado AS 

Select * from vFEVentaRD

union all

Select * from vFEDevCORD

union all

Select * from vFEDevCRRD

union all

Select * from vFENCDIRD 

--Dolares

union all

Select * from vFEVentaUS

Union all

Select * from vFENCDIUS

Union All

Select * from vFEDevCRUS

Union All

Select * from vFEDevCORD



