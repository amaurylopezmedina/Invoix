Select estadofiscal,ncf,ResultadoEstadoFiscal,* from transa01 where estadofiscal is not null  order by fechacreacion desc


update transa01 set estadofiscal = 5  where estadofiscal is not null and fecha < '20250523' 

Select * from vfeencabezado where estadofiscal is not null and fechaemision >= '20250523' 


