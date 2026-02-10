

Select estadofiscal,ResultadoEstadoFiscal,trackid,codigoseguridad,* from FEEncabezado where  Trackid is null  order by fechacreacion
Select encf,MontoItem,PrecioUnitarioItem,CantidadItem,DescuentoMonto,(MontoItem/1.18),* from vfedetalle where encf ='E310000000105'

select * from vFEEncabezado

update FEENCABEZADO set estadofiscal = 1 , trackid =null,  ResultadoEstadoFiscal = null, FechaVencimientoSecuencia = '20251231'

select fechaemision,* from vfeencabezado   where  rncemisor = '131695312' and encf = 'E340000001001'

select * from vfedetalle   where  rncemisor = '131695312' and encf = 'E340000001001'

select * from fedetalle   where  rncemisor = '131695312' and encf = 'E340000000001'
/*
UPDATE FEENCABEZADO
SET ENCF = 
    LEFT(ENCF, PATINDEX('%[0-9]%', ENCF) - 1) + 
    RIGHT(REPLICATE('0', LEN(ENCF) - PATINDEX('%[0-9]%', ENCF) + 1) + 
    CAST(CAST(SUBSTRING(ENCF, PATINDEX('%[0-9]%', ENCF), LEN(ENCF)) AS BIGINT) - 500 AS VARCHAR(20)), 
    LEN(ENCF) - PATINDEX('%[0-9]%', ENCF) + 1)


UPDATE FEdetalle
SET ENCF = 
    LEFT(ENCF, PATINDEX('%[0-9]%', ENCF) - 1) + 
    RIGHT(REPLICATE('0', LEN(ENCF) - PATINDEX('%[0-9]%', ENCF) + 1) + 
    CAST(CAST(SUBSTRING(ENCF, PATINDEX('%[0-9]%', ENCF), LEN(ENCF)) AS BIGINT) - 500 AS VARCHAR(20)), 
    LEN(ENCF) - PATINDEX('%[0-9]%', ENCF) + 1)

*/

