create
or alter view VFEDetalle as
Select
    *
from
    vFEDetalleTransa01
with
    (nolock)
union all
Select
    *
from
    VFEDetalleCXCMovi1Devolucion
with
    (nolock)
union all
Select
    *
from
    VFEDetalleCXCMovi1Directa
with
    (nolock)
Union all
Select
    *
from
    VFEDetalleCXCMovi2Devolucion
with
    (nolock)
union all
Select
    *
from
    VFEDetalleCXCMovi2Directa
with
    (nolock)
    /*
    Union All
    
    Select * from VFEDetalleCajaChica
    
    Union All
    
    Select * from VFEDetalleCXPMovi1
    
    Union all
    
    Select * from VFEDetalleCXCMovi2 */