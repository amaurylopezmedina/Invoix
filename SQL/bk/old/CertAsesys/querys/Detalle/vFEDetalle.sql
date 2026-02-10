create or alter view VFEDetalle as

Select * from vFEDetalleTransa01

union all

Select * from VFEDetalleCXCMovi1Devolucion

union all

Select * from VFEDetalleCXCMovi1Directa

Union All

Select * from VFEDetalleCXPMovi1


Union All

Select * from VFEDetalleCajaChica

