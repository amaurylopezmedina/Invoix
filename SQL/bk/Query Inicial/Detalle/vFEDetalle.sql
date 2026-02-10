create or alter view vFEDetalle as

Select * from vFEVentaDetRD

union all

Select * from vFEDevCODetRD

union all

Select * from vFEDevCRDetRD

union all
Select * from vFENCDIDEtRD