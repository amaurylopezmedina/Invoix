create or alter view vFEDetalle as

Select * from vFEVentaDetRD

union all

Select * from vFEDevCODetRD

union all

Select * from vFEDevCRDetRD

union all

Select * from vFENCDIDEtRD

--Dolares

union all

Select * from  vFEVentaDetUS


union all

Select * from vFEDevCODetUS


union all

Select * from vFENCDIDEtUS


union all

Select * from vFENCDIDEtUS
