create or alter view vFEDetalle as

Select * from vFEVentaDetRD

union all

Select * from vFEVentaDetUS

union all

Select * from vFEDevCODetRD

union all

Select * from vFEDevCRDetRD

union all

Select * from vFENCDIDEtRD

Union all

--Gastos Menores
Select * from vFEDetGASMENCXP

Union all

Select * from vFEDetGASMENCC

--Compras Informales

Union all

Select * from vFEDetallePI
